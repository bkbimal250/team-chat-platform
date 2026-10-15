"""Real PostgreSQL OTP/session saga tests with deterministic internal HTTP boundaries."""

import asyncio
import hashlib
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.errors import DomainError
from app.db.base import Base
from app.db.session import get_session
from app.main import app
from app.models.models import Identity, InvitationOnboarding, OTPChallenge, OutboxEvent


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
async def invitation_harness(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with sessions() as session:
            yield session

    app.dependency_overrides[get_session] = dependency
    app.state.redis = Redis()
    secret = uuid4().hex + uuid4().hex
    phone = "+9198" + str(uuid4().int % 100000000).zfill(8)
    data = {
        "invitation_id": str(uuid4()),
        "organization_id": str(uuid4()),
        "company_name": "Inviting Company",
        "recipient_name": "Invited Employee",
        "phone": phone,
        "expires_at": (datetime.now(UTC) + timedelta(hours=48)).isoformat(),
    }
    state = {"secret": secret, "status": "PENDING", "member_id": str(uuid4()), "fail": False}
    calls = []

    async def organization(action, payload, correlation_id):
        if action == "validate":
            if payload["token"] != state["secret"]:
                raise DomainError("INVITATION_INVALID", "Invalid invitation.", 404)
            if state["status"] != "PENDING":
                raise DomainError("INVITATION_" + state["status"], "Invitation unavailable.", 410)
            return data.copy()
        if action == "resume":
            assert state["status"] == "ACCEPTED" and payload["phone"] == phone
            assert payload["token_hash"] == hashlib.sha256(state["secret"].encode()).hexdigest()
            return data.copy()
        calls.append(("organization", payload.copy()))
        assert payload["phone"] == phone and payload["invitation_id"] == data["invitation_id"]
        if payload["token_hash"] != hashlib.sha256(state["secret"].encode()).hexdigest():
            raise DomainError("INVITATION_INVALID", "Invalid invitation.", 404)
        if state["status"] in {"REVOKED", "EXPIRED"}:
            raise DomainError("INVITATION_" + state["status"], "Invitation unavailable.", 410)
        if state["fail"]:
            raise DomainError("PROVISIONING_RETRY", "Retry provisioning.", 503)
        state["status"] = "ACCEPTED"
        return {"organization_id": data["organization_id"], "member_id": state["member_id"]}

    async def provision(service, route, payload, correlation_id):
        assert service == "user" and route == "/internal/v1/users/provision"
        calls.append(("user", payload.copy()))
        return {"user_id": payload["identity_id"]}

    monkeypatch.setattr("app.api.v1.invitations.organization", organization)
    monkeypatch.setattr("app.api.v1.invitations.provision", provision)
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, sessions, data, state, calls
    app.dependency_overrides.clear()
    await engine.dispose()


async def request(harness):
    client, _, _, state, _ = harness
    result = await client.post("/api/v1/auth/invitations/request", json={"token": state["secret"]})
    assert result.status_code == 202
    return result.json()


def verification(challenge, **extra):
    return {
        "onboarding_id": challenge["onboarding_id"],
        "otp": challenge["development_code"],
        "device": {
            "installation_id": uuid4().hex,
            "platform": "WEB",
            "device_name": "Employee Browser",
        },
        **extra,
    }


@pytest.mark.asyncio
async def test_public_validation_minimal_masked_and_no_secrets(invitation_harness):
    client, _, data, state, _ = invitation_harness
    response = await client.post(
        "/api/v1/auth/invitations/validate", json={"token": state["secret"]}
    )
    body = response.json()
    assert response.status_code == 200 and body["valid"]
    assert set(body) == {
        "valid",
        "company_name",
        "recipient_name",
        "recipient_phone_masked",
        "expires_at",
    }
    assert data["phone"] not in response.text and state["secret"] not in response.text


@pytest.mark.asyncio
async def test_new_identity_session_and_completed_otp_replay(invitation_harness, caplog):
    client, sessions, data, _, calls = invitation_harness
    challenge = await request(invitation_harness)
    body = verification(challenge)
    response = await client.post("/api/v1/auth/invitations/verify", json=body)
    assert (
        response.status_code == 200
        and response.json()["access_token"]
        and response.json()["refresh_token"]
    )
    assert response.json()["organization_id"] == data["organization_id"]
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        identity = await db.get(Identity, row.identity_id)
        assert row.state == "COMPLETED" and row.verified_code_hash is None
        assert identity.status == "ACTIVE" and identity.phone_verified
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Identity)
                .where(Identity.phone_number == data["phone"])
            )
            == 1
        )
        assert (
            await db.scalar(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.aggregate_id == identity.id,
                    OutboxEvent.event_type == "identity.created.v1",
                )
            )
            == 1
        )
    assert data["phone"] not in caplog.text and body["otp"] not in caplog.text
    assert [call[0] for call in calls] == ["user", "organization"]
    assert (await client.post("/api/v1/auth/invitations/verify", json=body)).status_code == 409
    assert (
        await client.post(
            "/api/v1/auth/otp/verify",
            json={
                "challenge_id": str(row.challenge_id),
                "code": body["otp"],
                "device": body["device"],
            },
        )
    ).status_code == 409


@pytest.mark.asyncio
async def test_existing_identity_reused_without_identity_created_event(invitation_harness):
    client, sessions, data, _, calls = invitation_harness
    async with sessions() as db, db.begin():
        identity = Identity(
            phone_number=data["phone"],
            phone_verified=True,
            email="existing-" + uuid4().hex + "@example.test",
            status="ACTIVE",
        )
        db.add(identity)
        await db.flush()
        identity_id = identity.id
    challenge = await request(invitation_harness)
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 200
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        assert row.identity_id == identity_id
        assert (await db.get(Identity, identity_id)).email == identity.email
        assert (
            await db.scalar(
                select(func.count())
                .select_from(OutboxEvent)
                .where(
                    OutboxEvent.aggregate_id == identity_id,
                    OutboxEvent.event_type == "identity.created.v1",
                )
            )
            == 0
        )
    assert calls[0][1]["identity_id"] == str(identity_id)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field",
    ["phone", "phone_number", "organization_id", "branch_id", "team_id", "role", "member_id"],
)
async def test_authority_tampering_rejected(invitation_harness, field):
    client, _, _, state, _ = invitation_harness
    assert (
        await client.post(
            "/api/v1/auth/invitations/request", json={"token": state["secret"], field: str(uuid4())}
        )
    ).status_code == 422
    challenge = await request(invitation_harness)
    response = await client.post(
        "/api/v1/auth/invitations/verify", json=verification(challenge, **{field: str(uuid4())})
    )
    assert response.status_code == 422 and state["status"] == "PENDING"


@pytest.mark.asyncio
@pytest.mark.parametrize("status", ["REVOKED", "EXPIRED", "ACCEPTED"])
async def test_unavailable_invitation_request_rejected(invitation_harness, status):
    client, _, _, state, _ = invitation_harness
    state["status"] = status
    result = await client.post("/api/v1/auth/invitations/request", json={"token": state["secret"]})
    assert result.status_code == 410


@pytest.mark.asyncio
async def test_random_and_malformed_tokens_rejected(invitation_harness):
    client, _, _, _, _ = invitation_harness
    for secret, status in [("invalid", 422), ("a" * 43, 404)]:
        assert (
            await client.post("/api/v1/auth/invitations/validate", json={"token": secret})
        ).status_code == status


@pytest.mark.asyncio
async def test_wrong_otp_committed_attempt_limit_and_no_identity(invitation_harness):
    client, sessions, _, _, calls = invitation_harness
    challenge = await request(invitation_harness)
    body = verification(challenge)
    body["otp"] = "000000" if body["otp"] != "000000" else "000001"
    for _ in range(5):
        assert (await client.post("/api/v1/auth/invitations/verify", json=body)).status_code == 400
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 429
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        otp = await db.get(OTPChallenge, row.challenge_id)
        assert otp.attempt_count == 5 and row.identity_id is None
    assert calls == []


@pytest.mark.asyncio
async def test_expired_otp_and_cooldown(invitation_harness):
    client, sessions, _, state, calls = invitation_harness
    challenge = await request(invitation_harness)
    assert (
        await client.post("/api/v1/auth/invitations/resend", json={"token": state["secret"]})
    ).status_code == 429
    async with sessions() as db, db.begin():
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        otp = await db.get(OTPChallenge, row.challenge_id)
        otp.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 400
    assert calls == []


@pytest.mark.asyncio
@pytest.mark.parametrize("state_change", ["REVOKED", "EXPIRED", "rotate"])
async def test_revocation_or_rotation_after_otp_cannot_create_access(
    invitation_harness, state_change
):
    client, sessions, _, state, _ = invitation_harness
    challenge = await request(invitation_harness)
    if state_change == "rotate":
        state["secret"] = uuid4().hex + uuid4().hex
    else:
        state["status"] = state_change
    result = await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    assert result.status_code in {404, 410} and "access_token" not in result.json()
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        assert row.state == "VERIFIED" and row.member_id is None
        assert (await db.get(Identity, row.identity_id)).status == "PENDING"


@pytest.mark.asyncio
async def test_failure_retry_resumes_durable_intent_once(invitation_harness):
    client, sessions, _, state, _ = invitation_harness
    challenge = await request(invitation_harness)
    body = verification(challenge)
    state["fail"] = True
    assert (await client.post("/api/v1/auth/invitations/verify", json=body)).status_code == 503
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        identity_id = row.identity_id
        assert row.state == "VERIFIED" and row.last_error == "PROVISIONING_RETRY"
    resumed = await client.post("/api/v1/auth/invitations/request", json={"token": state["secret"]})
    assert resumed.status_code == 202 and resumed.json()["verified"]
    assert resumed.json()["onboarding_id"] == challenge["onboarding_id"]
    state["fail"] = False
    assert (await client.post("/api/v1/auth/invitations/verify", json=body)).status_code == 200
    async with sessions() as db:
        assert (await db.get(InvitationOnboarding, row.id)).identity_id == identity_id


@pytest.mark.asyncio
async def test_parallel_acceptance_at_most_one_session_result(invitation_harness):
    client, sessions, data, _, _ = invitation_harness
    challenge = await request(invitation_harness)
    body = verification(challenge)
    results = await asyncio.gather(
        *(client.post("/api/v1/auth/invitations/verify", json=body) for _ in range(2))
    )
    assert sorted(result.status_code for result in results) == [200, 409]
    async with sessions() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(Identity)
                .where(Identity.phone_number == data["phone"])
            )
            == 1
        )


@pytest.mark.asyncio
async def test_refresh_can_resume_after_remote_acceptance_before_session(
    invitation_harness, monkeypatch
):
    from app.services.session_service import SessionService

    client, _, _, state, _ = invitation_harness
    challenge = await request(invitation_harness)
    original = SessionService.create

    async def unavailable(*args, **kwargs):
        raise DomainError("PROVISIONING_RETRY", "Retry session completion.", 503)

    monkeypatch.setattr(SessionService, "create", unavailable)
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 503
    assert state["status"] == "ACCEPTED"
    assert (
        await client.post("/api/v1/auth/invitations/validate", json={"token": state["secret"]})
    ).status_code == 200
    resumed = await client.post("/api/v1/auth/invitations/request", json={"token": state["secret"]})
    assert resumed.status_code == 202 and resumed.json()["verified"]
    assert resumed.json()["onboarding_id"] == challenge["onboarding_id"]
    monkeypatch.setattr(SessionService, "create", original)
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 200


@pytest.mark.asyncio
async def test_rotated_verified_reservation_reuses_identity_after_new_phone_proof(
    invitation_harness,
):
    client, sessions, _, state, _ = invitation_harness
    challenge = await request(invitation_harness)
    state["fail"] = True
    assert (
        await client.post("/api/v1/auth/invitations/verify", json=verification(challenge))
    ).status_code == 503
    async with sessions() as db:
        row = await db.get(InvitationOnboarding, UUID(challenge["onboarding_id"]))
        identity_id = row.identity_id
    state["secret"] = uuid4().hex + uuid4().hex
    state["fail"] = False
    app.state.redis.cooldowns.clear()  # Test fake models elapsed cooldown; real limits are unchanged.
    replacement = await request(invitation_harness)
    assert replacement["onboarding_id"] == challenge["onboarding_id"]
    result = await client.post("/api/v1/auth/invitations/verify", json=verification(replacement))
    assert result.status_code == 200
    async with sessions() as db:
        assert (await db.get(InvitationOnboarding, row.id)).identity_id == identity_id


@pytest.mark.asyncio
async def test_invalid_invitation_requests_are_rate_limited_before_upstream(invitation_harness):
    client, _, _, _, calls = invitation_harness
    for _ in range(10):
        assert (
            await client.post("/api/v1/auth/invitations/request", json={"token": "a" * 43})
        ).status_code == 404
    assert (
        await client.post("/api/v1/auth/invitations/request", json={"token": "a" * 43})
    ).status_code == 429
    assert calls == []
