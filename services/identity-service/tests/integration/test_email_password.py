import asyncio
import os
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.base import Base
from app.db.session import get_session
from app.integrations.otp_provider import DevelopmentOTPProvider, VonageVerifyOTPProvider
from app.main import app
from app.models.models import CompanyRegistration, Identity, OTPChallenge
from app.security.hashing import verify_secret


class Redis:
    def __init__(self):
        self.counts = defaultdict(int)

    async def incr(self, key):
        self.counts[key] += 1
        return self.counts[key]

    async def expire(self, *args):
        return True

    async def ttl(self, key):
        return 3600


@pytest_asyncio.fixture
async def harness(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with factory() as db:
            yield db

    app.dependency_overrides[get_session] = dependency
    app.state.redis = Redis()
    monkeypatch.setattr(get_settings(), "AUTH_PHONE_OTP_ENABLED", False)
    for provider in [DevelopmentOTPProvider, VonageVerifyOTPProvider]:
        monkeypatch.setattr(
            provider, "send_otp", AsyncMock(side_effect=AssertionError("OTP must not be sent"))
        )
    calls = []
    member = uuid4()

    async def provision(service, route, payload, correlation_id):
        calls.append(payload)
        return (
            {"user_id": payload["identity_id"]}
            if service == "user"
            else {"organization_id": payload["organization_id"], "member_id": str(member)}
        )

    async def memberships(self, identity_id, correlation_id):
        async with factory() as db:
            row = await db.scalar(
                select(CompanyRegistration).where(CompanyRegistration.identity_id == identity_id)
            )
            return [
                SimpleNamespace(
                    status="ACTIVE", organization_id=row.organization_id, member_id=member
                )
            ]

    monkeypatch.setattr("app.api.v1.registration.provision", provision)
    monkeypatch.setattr(
        "app.integrations.organization_service.OrganizationServiceClient.memberships", memberships
    )
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, factory, calls
    app.dependency_overrides.clear()
    await engine.dispose()


def body():
    return {
        "company_name": "Email Company",
        "owner_name": "Email Owner",
        "email": uuid4().hex + "@example.test",
        "phone": "+9198" + str(uuid4().int % 100000000).zfill(8),
        "password": "A long password with spaces!",
        "device": {"installation_id": uuid4().hex, "platform": "WEB", "device_name": "Email test"},
    }


@pytest.mark.asyncio
async def test_registration_login_refresh_logout_and_no_otp(harness, caplog):
    client, factory, calls = harness
    payload = body()
    async with factory() as db:
        before = await db.scalar(select(func.count()).select_from(OTPChallenge))
    response = await client.post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 201
    tokens = response.json()
    assert len(calls) == 2
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        assert identity.password_hash.startswith("$argon2id$")
        assert verify_secret(payload["password"], identity.password_hash)
        assert not identity.phone_verified and not identity.email_verified
        assert await db.scalar(select(func.count()).select_from(OTPChallenge)) == before
    assert payload["password"] not in caplog.text
    assert VonageVerifyOTPProvider.send_otp.await_count == 0
    assert DevelopmentOTPProvider.send_otp.await_count == 0
    assert "password" not in tokens and "password_hash" not in tokens
    login = {k: payload[k] for k in ["email", "password", "device"]}
    login["email"] = "  " + payload["email"].upper() + "  "
    result = await client.post("/api/v1/auth/login", json=login)
    assert result.status_code == 200
    assert result.json()["organization_id"] is None
    scoped = await client.post(
        "/api/v1/auth/login",
        json={**login, "organization_id": tokens["organization_id"]},
    )
    assert scoped.status_code == 200
    assert scoped.json()["organization_id"] == tokens["organization_id"]
    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": result.json()["refresh_token"]}
    )
    assert refresh.status_code == 200
    logout = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": "Bearer " + refresh.json()["access_token"]},
        json={},
    )
    assert logout.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/otp/request", json={"phone_number": payload["phone"], "purpose": "LOGIN"}
        )
    ).json()["error"]["code"] == "PHONE_OTP_DISABLED"


@pytest.mark.asyncio
async def test_invalid_unknown_and_wrong_password_are_generic(harness):
    client, _, _ = harness
    payload = body()
    assert (await client.post("/api/v1/auth/registration/company", json=payload)).status_code == 201
    login = {k: payload[k] for k in ["email", "password", "device"]}
    login["password"] = "wrong password"
    wrong = await client.post("/api/v1/auth/login", json=login)
    login["email"] = uuid4().hex + "@example.test"
    unknown = await client.post("/api/v1/auth/login", json=login)
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["error"]["message"] == unknown.json()["error"]["message"]


@pytest.mark.asyncio
async def test_duplicate_and_concurrent_registration(harness):
    client, _, calls = harness
    payload = body()
    results = await asyncio.gather(
        *[client.post("/api/v1/auth/registration/company", json=payload) for _ in range(2)]
    )
    assert sorted(r.status_code for r in results) == [201, 409]
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_partial_provisioning_resumes_same_identity(harness, monkeypatch):
    client, factory, calls = harness
    from app.api.v1 import registration

    original = registration.provision

    async def failed(*args):
        raise DomainError("PROVISIONING_RETRY", "Unavailable", 503)

    monkeypatch.setattr(registration, "provision", failed)
    payload = body()
    assert (await client.post("/api/v1/auth/registration/company", json=payload)).status_code == 503
    async with factory() as db:
        original_id = await db.scalar(select(Identity.id).where(Identity.email == payload["email"]))
    monkeypatch.setattr(registration, "provision", original)
    assert (await client.post("/api/v1/auth/registration/company", json=payload)).status_code == 201
    assert UUID(calls[0]["identity_id"]) == original_id


@pytest.mark.parametrize(
    "field,value", [("email", "invalid"), ("password", "short"), ("phone", "invalid")]
)
@pytest.mark.asyncio
async def test_validation(harness, field, value):
    payload = body()
    payload[field] = value
    response = await harness[0].post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 422
    assert "input" not in str(response.json())


@pytest.mark.asyncio
async def test_login_rate_limit(harness):
    client, _, _ = harness
    payload = body()
    digest = __import__("hashlib").sha256(payload["email"].encode()).hexdigest()
    app.state.redis.counts[f"password:login:email:{digest}"] = 20
    response = await client.post(
        "/api/v1/auth/login", json={k: payload[k] for k in ["email", "password", "device"]}
    )
    assert response.status_code == 429


@pytest.mark.asyncio
async def test_disabled_and_otp_only_accounts_cannot_password_login(harness):
    client, factory, _ = harness
    payload = body()
    assert (await client.post("/api/v1/auth/registration/company", json=payload)).status_code == 201
    async with factory.begin() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        identity.status = "DISABLED"
    login = {k: payload[k] for k in ["email", "password", "device"]}
    assert (await client.post("/api/v1/auth/login", json=login)).json()["error"][
        "code"
    ] == "INVALID_CREDENTIALS"
    async with factory.begin() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        identity.status, identity.password_hash = "ACTIVE", None
    login["password"] = "non-account dummy password"
    assert (await client.post("/api/v1/auth/login", json=login)).json()["error"][
        "code"
    ] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_email_feature_gate_and_password_not_in_validation_response(harness, monkeypatch):
    client, _, _ = harness
    monkeypatch.setattr(get_settings(), "AUTH_EMAIL_PASSWORD_ENABLED", False)
    payload = body()
    response = await client.post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "EMAIL_PASSWORD_DISABLED"
    monkeypatch.setattr(get_settings(), "AUTH_EMAIL_PASSWORD_ENABLED", True)
    payload["password"] = "secret-too-short"
    payload["unexpected"] = "secret-that-must-not-escape"
    response = await client.post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text and payload["unexpected"] not in response.text


@pytest.mark.asyncio
async def test_invitation_password_binding_retry_and_existing_account(harness, monkeypatch):
    client, factory, _ = harness
    from app.api.v1 import invitations

    email = uuid4().hex + "@example.test"
    invite_id, organization_id, member_id = uuid4(), uuid4(), uuid4()
    token = "a" + uuid4().hex + uuid4().hex
    calls = []

    async def organization(action, payload, correlation_id):
        calls.append((action, payload))
        if action == "validate":
            return {
                "invitation_id": str(invite_id),
                "organization_id": str(organization_id),
                "company_name": "Company",
                "recipient_name": "Employee",
                "phone": "",
                "email": email,
                "expires_at": (datetime.now(UTC) + timedelta(hours=1)).isoformat(),
            }
        return {"organization_id": str(organization_id), "member_id": str(member_id)}

    monkeypatch.setattr(invitations, "organization", organization)
    payload = {
        "token": token,
        "email": "other@example.test",
        "password": "Long password with spaces!",
        "device": body()["device"],
    }
    assert (await client.post("/api/v1/auth/invitations/password", json=payload)).status_code == 403
    payload["email"] = email
    response = await client.post("/api/v1/auth/invitations/password", json=payload)
    assert response.status_code == 200
    assert calls[-1][0] == "accept-email"
    assert (await client.post("/api/v1/auth/invitations/password", json=payload)).status_code == 409
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == email))
        original_hash = identity.password_hash
        assert not identity.phone_verified
    # A second invitation authenticates the existing account; it cannot change its hash.
    invite_id = uuid4()
    payload["token"] = "b" + uuid4().hex + uuid4().hex
    payload["password"] = "Incorrect existing password"
    assert (await client.post("/api/v1/auth/invitations/password", json=payload)).status_code == 401
    payload["password"] = "Long password with spaces!"
    assert (await client.post("/api/v1/auth/invitations/password", json=payload)).status_code == 200
    async with factory() as db:
        assert (
            await db.scalar(select(Identity.password_hash).where(Identity.email == email))
            == original_hash
        )
