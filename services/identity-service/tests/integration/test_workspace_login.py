"""Personal default login, explicit org selection, and membership lifecycle."""

import os
from collections import defaultdict
from types import SimpleNamespace
from uuid import UUID, uuid4

import httpx
import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import get_settings
from app.db.base import Base
from app.db.session import get_session
from app.events.consumers import apply_membership_event
from app.main import app
from app.models.models import CompanyRegistration, Identity

from .test_email_password import Redis, body
from .test_personal_accounts import personal_body


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
    member_a, member_b = uuid4(), uuid4()
    org_a, org_b = uuid4(), uuid4()
    state = {"memberships": []}
    provision_member = uuid4()

    async def provision(service, route, payload, correlation_id):
        if service == "user":
            return {"user_id": payload["identity_id"]}
        return {
            "organization_id": payload["organization_id"],
            "member_id": str(provision_member),
        }

    async def memberships(self, identity_id, correlation_id):
        return list(state["memberships"])

    monkeypatch.setattr("app.api.v1.registration.provision", provision)
    monkeypatch.setattr(
        "app.integrations.organization_service.OrganizationServiceClient.memberships", memberships
    )
    monkeypatch.setattr(
        "app.services.login_context.OrganizationServiceClient.memberships", memberships
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client, factory, state, org_a, org_b, member_a, member_b, provision_member
    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_password_login_defaults_personal_after_member_removed(harness):
    client, factory, state, _, _, member_a, _, provision_member = harness
    payload = body()
    registered = await client.post("/api/v1/auth/registration/company", json=payload)
    assert registered.status_code == 201
    tokens = registered.json()
    org_id = UUID(tokens["organization_id"])
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        identity_id = identity.id
        row = await db.scalar(
            select(CompanyRegistration).where(CompanyRegistration.identity_id == identity_id)
        )
        org_id = row.organization_id
    state["memberships"] = [
        SimpleNamespace(status="ACTIVE", organization_id=org_id, member_id=provision_member)
    ]
    login = {k: payload[k] for k in ["email", "password", "device"]}
    with_org = await client.post(
        "/api/v1/auth/login", json={**login, "organization_id": str(org_id)}
    )
    assert with_org.status_code == 200
    assert with_org.json()["organization_id"] == str(org_id)
    async with factory() as db:
        await apply_membership_event(
            db,
            {
                "event_id": str(uuid4()),
                "event_type": "member.removed.v2",
                "producer": "organization",
                "organization_id": str(org_id),
                "payload": {
                    "member_id": str(provision_member),
                    "identity_id": str(identity_id),
                },
            },
        )
        await db.commit()
    state["memberships"] = []
    personal = await client.post("/api/v1/auth/login", json=login)
    assert personal.status_code == 200
    assert personal.json()["organization_id"] is None and personal.json()["member_id"] is None
    async with factory() as db:
        assert await db.get(Identity, identity_id) is not None


@pytest.mark.asyncio
async def test_multi_org_requires_explicit_organization_selection(harness):
    client, factory, state, org_a, org_b, member_a, member_b, _ = harness
    data = personal_body()
    assert (await client.post("/api/v1/auth/registration/personal", json=data)).status_code == 201
    state["memberships"] = [
        SimpleNamespace(status="ACTIVE", organization_id=org_a, member_id=member_a),
        SimpleNamespace(status="ACTIVE", organization_id=org_b, member_id=member_b),
    ]
    login = {k: data[k] for k in ("email", "password", "device")}
    personal = await client.post("/api/v1/auth/login", json=login)
    assert personal.status_code == 200
    assert personal.json()["organization_id"] is None
    first = await client.post(
        "/api/v1/auth/login", json={**login, "organization_id": str(org_a)}
    )
    second = await client.post(
        "/api/v1/auth/login", json={**login, "organization_id": str(org_b)}
    )
    assert first.status_code == 200 and UUID(first.json()["member_id"]) == member_a
    assert second.status_code == 200 and UUID(second.json()["member_id"]) == member_b
    unknown = await client.post(
        "/api/v1/auth/login", json={**login, "organization_id": str(uuid4())}
    )
    assert unknown.status_code == 403


@pytest.mark.asyncio
async def test_otp_login_personal_without_membership(harness, monkeypatch):
    client, factory, state, *_ = harness
    monkeypatch.setattr(get_settings(), "AUTH_PHONE_OTP_ENABLED", True)
    monkeypatch.setattr(get_settings(), "REGISTRATION_POLICY", "open")
    phone = "+9198" + str(uuid4().int % 100000000).zfill(8)
    device = {"installation_id": uuid4().hex, "platform": "WEB", "device_name": "OTP test"}
    requested = await client.post(
        "/api/v1/auth/otp/request", json={"phone_number": phone, "purpose": "LOGIN"}
    )
    assert requested.status_code == 202
    challenge_id = requested.json()["challenge_id"]
    code = requested.json()["development_code"]
    verified = await client.post(
        "/api/v1/auth/otp/verify",
        json={"challenge_id": challenge_id, "code": code, "device": device},
    )
    assert verified.status_code == 200
    assert verified.json()["organization_id"] is None
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.phone_number == phone))
        assert identity is not None and identity.phone_verified
