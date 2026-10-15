"""Personal accounts use real PostgreSQL sessions without fabricated tenancy."""

from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select

from app.core.errors import DomainError
from app.models.models import CompanyRegistration, Identity, PersonalRegistration, Session
from app.security.hashing import verify_secret
from app.security.tokens import decode_access_token

from .test_email_password import body
from .test_email_password import harness as harness


def personal_body():
    data = body()
    data.pop("company_name")
    data["display_name"] = data.pop("owner_name")
    return data


@pytest.mark.asyncio
async def test_personal_registration_login_refresh_devices_and_logout(harness, monkeypatch):
    client, factory, calls = harness
    memberships = AsyncMock(
        side_effect=AssertionError("Personal login must not depend on Organization")
    )
    monkeypatch.setattr(
        "app.integrations.organization_service.OrganizationServiceClient.memberships", memberships
    )
    data = personal_body()
    response = await client.post("/api/v1/auth/registration/personal", json=data)
    assert response.status_code == 201, response.text
    tokens = response.json()
    assert tokens["organization_id"] is None and tokens["member_id"] is None
    claims = decode_access_token(tokens["access_token"])
    assert "org" not in claims and "mid" not in claims
    assert calls == [{"identity_id": claims["sub"], "display_name": data["display_name"]}]
    async with factory() as db:
        identity = await db.get(Identity, UUID(claims["sub"]))
        assert identity.status == "ACTIVE"
        assert identity.phone_number == data["phone"]
        assert not identity.phone_verified and not identity.email_verified
        assert identity.password_hash.startswith("$argon2id$")
        assert verify_secret(data["password"], identity.password_hash)
        assert (
            await db.scalar(
                select(CompanyRegistration.id).where(CompanyRegistration.identity_id == identity.id)
            )
            is None
        )
        session = await db.get(Session, UUID(tokens["session_id"]))
        assert session.organization_id is None and session.member_id is None
    headers = {"Authorization": "Bearer " + tokens["access_token"]}
    assert (await client.get("/api/v1/auth/me", headers=headers)).json()["context"] == {
        "organization_id": None,
        "member_id": None,
    }
    devices = await client.get("/api/v1/devices", headers=headers)
    assert devices.status_code == 200 and len(devices.json()) == 1
    assert (await client.get("/api/v1/platform/me", headers=headers)).status_code == 403
    login = await client.post(
        "/api/v1/auth/login", json={key: data[key] for key in ("email", "password", "device")}
    )
    assert login.status_code == 200 and login.json()["organization_id"] is None
    refreshed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login.json()["refresh_token"]}
    )
    assert refreshed.status_code == 200 and refreshed.json()["member_id"] is None
    headers = {"Authorization": "Bearer " + refreshed.json()["access_token"]}
    assert (await client.post("/api/v1/auth/logout", headers=headers, json={})).status_code == 200
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 401
    memberships.assert_not_awaited()


@pytest.mark.asyncio
async def test_failed_personal_profile_provision_resumes_same_identity(harness, monkeypatch):
    client, factory, calls = harness
    from app.api.v1 import registration

    original = registration.provision
    monkeypatch.setattr(
        registration,
        "provision",
        AsyncMock(side_effect=DomainError("PROVISIONING_RETRY", "Unavailable", 503)),
    )
    data = personal_body()
    assert (await client.post("/api/v1/auth/registration/personal", json=data)).status_code == 503
    async with factory() as db:
        identity_id = await db.scalar(select(Identity.id).where(Identity.email == data["email"]))
        assert (await db.get(PersonalRegistration, identity_id)).completed_at is None
    monkeypatch.setattr(registration, "provision", original)
    result = await client.post("/api/v1/auth/registration/personal", json=data)
    assert result.status_code == 201
    assert UUID(calls[0]["identity_id"]) == identity_id
    assert (await client.post("/api/v1/auth/registration/personal", json=data)).status_code == 409
    async with factory() as db:
        assert (
            await db.scalar(
                select(func.count()).select_from(Identity).where(Identity.email == data["email"])
            )
            == 1
        )


@pytest.mark.asyncio
async def test_personal_duplicate_phone_and_unowned_workspace_are_denied(harness, monkeypatch):
    client, _, _ = harness
    data = personal_body()
    assert (await client.post("/api/v1/auth/registration/personal", json=data)).status_code == 201
    duplicate = {**data, "email": uuid4().hex + "@example.test"}
    assert (
        await client.post("/api/v1/auth/registration/personal", json=duplicate)
    ).status_code == 409
    monkeypatch.setattr(
        "app.integrations.organization_service.OrganizationServiceClient.memberships",
        AsyncMock(return_value=[]),
    )
    login = {key: data[key] for key in ("email", "password", "device")}
    login["organization_id"] = str(uuid4())
    assert (await client.post("/api/v1/auth/login", json=login)).status_code == 403


@pytest.mark.asyncio
async def test_personal_password_recovery_and_email_verification(harness):
    client, _, _ = harness
    data = personal_body()
    assert (await client.post("/api/v1/auth/registration/personal", json=data)).status_code == 201
    verification = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": data["email"]}
    )
    assert verification.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/email/verify",
            json={"token": verification.json()["development_verification_token"]},
        )
    ).status_code == 204

    reset = await client.post("/api/v1/auth/password/forgot", json={"email": data["email"]})
    assert reset.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/password/reset",
            json={
                "token": reset.json()["development_reset_token"],
                "new_password": "Another secure password 456!",
            },
        )
    ).status_code == 204


@pytest.mark.asyncio
async def test_personal_qr_linking_keeps_personal_context(harness):
    client, _, _ = harness
    data = personal_body()
    result = await client.post("/api/v1/auth/registration/personal", json=data)
    assert result.status_code == 201
    headers = {"Authorization": "Bearer " + result.json()["access_token"]}
    new_device = {**data["device"], "installation_id": uuid4().hex}
    challenge = await client.post("/api/v1/auth/qr/challenges", json=new_device)
    assert challenge.status_code == 201
    challenge_data = challenge.json()
    proof = {"secret": challenge_data["payload"].rsplit(".", 1)[1]}
    path = "/api/v1/auth/qr/challenges/" + challenge_data["challenge_id"]
    assert (await client.post(path + "/authorize", headers=headers, json=proof)).status_code == 200
    linked = await client.post(path + "/consume", json=proof)
    assert linked.status_code == 200
    assert linked.json()["organization_id"] is None and linked.json()["member_id"] is None
    devices = await client.get("/api/v1/devices", headers=headers)
    assert len(devices.json()) == 2
