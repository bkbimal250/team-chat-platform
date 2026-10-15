"""Real PostgreSQL orchestration persistence with service-owned HTTP adapters faked."""

import asyncio
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.v1.registration import RegistrationStart
from app.core.errors import DomainError
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.models import CompanyRegistration, Identity, OTPChallenge


class Redis:
    def __init__(self):
        self.counts = defaultdict(int)
        self.cooldowns = set()

    async def incr(self, key):
        self.counts[key] += 1
        return self.counts[key]

    async def ttl(self, key):
        return 60 if key in self.cooldowns else 3600

    async def expire(self, *args):
        return True

    async def set(self, key, *args, **kwargs):
        if key in self.cooldowns:
            return False
        self.cooldowns.add(key)
        return True


@pytest_asyncio.fixture
async def harness(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = dependency
    app.state.redis = Redis()
    calls = []

    async def provision(service, route, payload, correlation_id):
        calls.append((service, payload))
        return (
            {"user_id": payload["identity_id"]}
            if service == "user"
            else {"organization_id": payload["organization_id"], "member_id": str(uuid4())}
        )

    monkeypatch.setattr("app.api.v1.registration.provision", provision)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, sessions, calls
    app.dependency_overrides.clear()
    await engine.dispose()


def body():
    return {
        "company_name": "Test Company",
        "owner_name": "Test Owner",
        "email": uuid4().hex + "@example.test",
        "phone": "+9198" + str(uuid4().int % 100000000).zfill(8),
    }


def verify_body(challenge, **extra):
    return {
        "registration_id": challenge["registration_id"],
        "otp": challenge["development_code"],
        "device": {
            "installation_id": uuid4().hex,
            "platform": "WEB",
            "device_name": "Test browser",
        },
        **extra,
    }


async def start(client):
    data = body()
    response = await client.post("/api/v1/auth/registration/company/start", json=data)
    assert response.status_code == 202, response.json().get("error", {}).get("code")
    return data, response.json()


@pytest.mark.parametrize(
    "field,value",
    [
        ("company_name", " "),
        ("company_name", "!!"),
        ("owner_name", " "),
        ("email", "bad"),
        ("email", "a b@example.test"),
        ("phone", "123"),
    ],
)
def test_invalid_registration_input(field, value):
    data = body()
    data[field] = value
    with pytest.raises((ValidationError, DomainError)):
        RegistrationStart(**data)


def test_normalized_registration_fields():
    data = body()
    data.update(email="OWNER@Example.TEST ", company_name=" Example   Company ")
    model = RegistrationStart(**data)
    assert model.email == "owner@example.test" and model.company_name == "Example Company"


@pytest.mark.asyncio
async def test_registration_creates_owner_then_completed_replay_rejected(harness):
    client, sessions, calls = harness
    data, challenge = await start(client)
    response = await client.post(
        "/api/v1/auth/registration/company/verify", json=verify_body(challenge)
    )
    assert response.status_code == 200
    assert response.json()["access_token"] and response.json()["refresh_token"]
    async with sessions() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        identity = await db.get(Identity, row.identity_id)
        assert (
            row.state == "COMPLETED"
            and identity.status == "ACTIVE"
            and identity.phone_verified
            and not identity.email_verified
        )
        assert row.verified_code_hash is None
    assert [c[0] for c in calls] == ["user", "organization"]
    repeat = await client.post(
        "/api/v1/auth/registration/company/verify", json=verify_body(challenge)
    )
    assert repeat.status_code == 409 and len(calls) == 2
    duplicate = await client.post("/api/v1/auth/registration/company/start", json=data)
    assert duplicate.status_code == 409
    data["phone"] = body()["phone"]
    assert (
        await client.post("/api/v1/auth/registration/company/start", json=data)
    ).status_code == 409


@pytest.mark.asyncio
async def test_wrong_otp_attempts_are_committed_and_locked(harness):
    client, sessions, _ = harness
    _, challenge = await start(client)
    invalid = verify_body(challenge)
    invalid["otp"] = "000000" if invalid["otp"] != "000000" else "000001"
    for _ in range(5):
        assert (
            await client.post("/api/v1/auth/registration/company/verify", json=invalid)
        ).status_code == 400
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=verify_body(challenge))
    ).status_code == 429
    async with sessions() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        otp = await db.get(OTPChallenge, row.challenge_id)
        assert otp.attempt_count == 5 and row.identity_id is None


@pytest.mark.asyncio
async def test_registration_expiry_guessing_and_tampering(harness):
    client, sessions, _ = harness
    _, challenge = await start(client)
    assert (
        await client.post(
            "/api/v1/auth/registration/company/verify",
            json=verify_body(challenge, organization_id=str(uuid4())),
        )
    ).status_code == 422
    guessed = verify_body(challenge)
    guessed["registration_id"] = str(uuid4())
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=guessed)
    ).status_code == 404
    async with sessions.begin() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=verify_body(challenge))
    ).status_code == 410


@pytest.mark.asyncio
async def test_resend_cooldown_replaces_authoritative_challenge(harness):
    client, sessions, _ = harness
    _, challenge = await start(client)
    path = "/api/v1/auth/registration/company/resend"
    payload = {"registration_id": challenge["registration_id"]}
    assert (await client.post(path, json=payload)).status_code == 429
    app.state.redis.cooldowns.clear()  # Test clock/cooldown fake, never production Redis.
    async with sessions() as db:
        old = (await db.get(CompanyRegistration, challenge["registration_id"])).challenge_id
    result = await client.post(path, json=payload)
    assert result.status_code == 202
    async with sessions() as db:
        assert (await db.get(CompanyRegistration, challenge["registration_id"])).challenge_id != old


@pytest.mark.asyncio
@pytest.mark.parametrize("failed_service", ["user", "organization"])
async def test_partial_failure_resumes_same_identity_and_company(
    harness, monkeypatch, failed_service
):
    client, sessions, calls = harness
    _, challenge = await start(client)

    async def failed(service, route, payload, correlation_id):
        if service == failed_service:
            raise DomainError("PROVISIONING_RETRY", "Retry safely.", 503)
        return {"user_id": payload["identity_id"]}

    monkeypatch.setattr("app.api.v1.registration.provision", failed)
    payload = verify_body(challenge)
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=payload)
    ).status_code == 503
    async with sessions() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        previous = (row.identity_id, row.organization_id)
        assert (
            row.state == "VERIFIED"
            and (await db.get(Identity, row.identity_id)).status == "PENDING"
        )

    async def recovered(service, route, data, correlation_id):
        calls.append((service, data))
        return (
            {"user_id": data["identity_id"]}
            if service == "user"
            else {"organization_id": data["organization_id"], "member_id": str(uuid4())}
        )

    monkeypatch.setattr("app.api.v1.registration.provision", recovered)
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=payload)
    ).status_code == 200
    async with sessions() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        assert (row.identity_id, row.organization_id) == previous


@pytest.mark.asyncio
async def test_double_verification_creates_one_session(harness):
    client, _, calls = harness
    _, challenge = await start(client)
    payload = verify_body(challenge)
    responses = await asyncio.gather(
        *(client.post("/api/v1/auth/registration/company/verify", json=payload) for _ in range(2))
    )
    assert sorted(r.status_code for r in responses) == [200, 409]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_registration_start_rate_limit(harness):
    client, _, _ = harness
    app.state.redis.counts["registration:start:127.0.0.1"] = 10
    assert (
        await client.post("/api/v1/auth/registration/company/start", json=body())
    ).status_code == 429


@pytest.mark.asyncio
async def test_expired_otp_is_rejected_without_creating_identity(harness):
    client, sessions, _ = harness
    _, challenge = await start(client)
    async with sessions.begin() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        otp = await db.get(OTPChallenge, row.challenge_id)
        otp.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    result = await client.post(
        "/api/v1/auth/registration/company/verify", json=verify_body(challenge)
    )
    assert result.status_code == 400 and result.json()["error"]["code"] == "OTP_EXPIRED"


@pytest.mark.asyncio
async def test_resume_code_attempt_limit_persists(harness, monkeypatch):
    client, sessions, _ = harness
    _, challenge = await start(client)

    async def failed(*args):
        raise DomainError("PROVISIONING_RETRY", "Retry safely.", 503)

    monkeypatch.setattr("app.api.v1.registration.provision", failed)
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=verify_body(challenge))
    ).status_code == 503
    invalid = verify_body(challenge)
    invalid["otp"] = "000000" if invalid["otp"] != "000000" else "000001"
    for _ in range(5):
        assert (
            await client.post("/api/v1/auth/registration/company/verify", json=invalid)
        ).status_code == 400
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=verify_body(challenge))
    ).status_code == 429
    async with sessions() as db:
        assert (
            await db.get(CompanyRegistration, challenge["registration_id"])
        ).resume_attempts == 5


@pytest.mark.asyncio
async def test_operator_recovery_only_after_real_otp_verification(harness, monkeypatch):
    from app import recover_registration

    client, sessions, _ = harness
    _, challenge = await start(client)
    monkeypatch.setattr(recover_registration, "SessionLocal", sessions)
    with pytest.raises(RuntimeError, match="already verified"):
        await recover_registration.recover(challenge["registration_id"])

    async def failed(*args):
        raise DomainError("PROVISIONING_RETRY", "Retry safely.", 503)

    monkeypatch.setattr("app.api.v1.registration.provision", failed)
    assert (
        await client.post("/api/v1/auth/registration/company/verify", json=verify_body(challenge))
    ).status_code == 503

    async def recovered(service, route, data, correlation_id):
        return (
            {"user_id": data["identity_id"]}
            if service == "user"
            else {"organization_id": data["organization_id"], "member_id": str(uuid4())}
        )

    monkeypatch.setattr("app.api.v1.registration.provision", recovered)
    async with sessions.begin() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    await recover_registration.recover(challenge["registration_id"])
    await recover_registration.recover(challenge["registration_id"])
    async with sessions() as db:
        row = await db.get(CompanyRegistration, challenge["registration_id"])
        assert (
            row.state == "COMPLETED"
            and (await db.get(Identity, row.identity_id)).status == "ACTIVE"
        )


@pytest.mark.asyncio
async def test_simultaneous_start_does_not_create_two_intents(harness):
    client, _, _ = harness
    data = body()
    responses = await asyncio.gather(
        *(client.post("/api/v1/auth/registration/company/start", json=data) for _ in range(2))
    )
    assert sorted(r.status_code for r in responses) == [202, 409]
