from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest

from app.api.v1.password import PLATFORM_SESSION_CONTEXT, canonical_email, platform_context
from app.api.v1.platform import (
    ROLE_PERMISSIONS,
    grant_permissions,
    identity_metadata,
    session_metadata,
)
from app.api.v1.platform import sessions as platform_sessions
from app.db.session import get_session
from app.main import app
from app.models.models import Device, Identity, PlatformGrant, Session
from app.security.dependencies import current_principal

PATHS = ["me", "identities", f"identities/{uuid4()}", "sessions", "audit"]


@pytest.mark.parametrize("path", PATHS)
async def test_platform_requires_real_bearer(path):
    async def db():
        yield AsyncMock()

    app.dependency_overrides[get_session] = db
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/platform/{path}")
        assert response.status_code == 401
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("tenant_role", ["OWNER", "ADMIN", "MEMBER"])
@pytest.mark.parametrize("path", PATHS)
async def test_tenant_roles_never_grant_platform_access(path, tenant_role):
    principal = SimpleNamespace(identity_id=uuid4(), tenant_role=tenant_role)
    database = AsyncMock()
    database.get.side_effect = [None, SimpleNamespace(status="ACTIVE")]

    async def db():
        yield database

    app.dependency_overrides[get_session] = db
    app.dependency_overrides[current_principal] = lambda: principal
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get(f"/api/v1/platform/{path}")
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()


@pytest.mark.parametrize("role", ["ADMIN", "SUPER_ADMIN"])
async def test_persistent_grant_me_and_revocation(role):
    identity_id = uuid4()
    grant = PlatformGrant(identity_id=identity_id, role=role, active=True)
    database = AsyncMock()
    database.get.side_effect = lambda model, key: (
        grant if model is PlatformGrant else SimpleNamespace(status="ACTIVE")
    )

    async def db():
        yield database

    app.dependency_overrides[get_session] = db
    app.dependency_overrides[current_principal] = lambda: SimpleNamespace(identity_id=identity_id)
    app.state.redis = SimpleNamespace(incr=AsyncMock(return_value=1), expire=AsyncMock())
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/platform/me")
            assert response.status_code == 200
            assert set(response.json()["permissions"]) == ROLE_PERMISSIONS[role]
            grant.active = False
            assert (await client.get("/api/v1/platform/me")).status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_suspended_unknown_role_fail_closed_and_privacy_allowlist():
    grant = SimpleNamespace(role="SUPER_ADMIN", active=True)
    assert not grant_permissions(grant, SimpleNamespace(status="SUSPENDED"))
    assert not grant_permissions(
        SimpleNamespace(role="OWNER", active=True), SimpleNamespace(status="ACTIVE")
    )
    row = Identity(
        id=uuid4(),
        email="safe@example.test",
        password_hash="DO_NOT_EXPOSE",
        phone_number="DO_NOT_EXPOSE",
        status="ACTIVE",
    )
    assert set(identity_metadata(row)) == {
        "id",
        "email",
        "status",
        "email_verified",
        "phone_verified",
        "created_at",
        "last_login_at",
    }
    assert "DO_NOT_EXPOSE" not in str(identity_metadata(row))
    assert "platform.sessions.read" not in ROLE_PERMISSIONS["ADMIN"]


def test_platform_session_metadata_is_a_safe_allowlist():
    identity_id, device_id = uuid4(), uuid4()
    session = Session(
        id=uuid4(),
        identity_id=identity_id,
        device_id=device_id,
        organization_id=uuid4(),
        member_id=uuid4(),
        status="ACTIVE",
        refresh_family_id=uuid4(),
        ip_address="DO_NOT_EXPOSE",
        user_agent="DO_NOT_EXPOSE",
    )
    device = Device(
        id=device_id,
        identity_id=identity_id,
        platform="WEB",
        device_name="Browser",
        installation_id="safe-installation",
    )
    data = session_metadata(session, device)
    assert set(data) == {
        "id",
        "identity_id",
        "device_id",
        "device_name",
        "platform",
        "device_status",
        "status",
        "created_at",
        "last_activity_at",
        "expires_at",
        "revoked_at",
    }
    assert "DO_NOT_EXPOSE" not in str(data)


@pytest.mark.asyncio
async def test_platform_sessions_filters_one_identity_and_paginates_server_side():
    identity_id, other_identity_id = uuid4(), uuid4()
    device_id = uuid4()
    identity = SimpleNamespace(id=identity_id)
    session = SimpleNamespace(
        id=uuid4(),
        identity_id=identity_id,
        device_id=device_id,
        status="ACTIVE",
        created_at="created",
        last_activity_at="active",
        expires_at="expires",
        revoked_at=None,
    )
    device = SimpleNamespace(device_name="Browser", platform="WEB", status="ACTIVE")
    database = AsyncMock()
    database.get.return_value = identity
    database.scalar.return_value = 23
    database.execute.return_value = SimpleNamespace(all=lambda: [(session, device)])

    result = await platform_sessions(
        identity_id=identity_id,
        limit=20,
        offset=20,
        access=(SimpleNamespace(identity_id=other_identity_id), None, frozenset()),
        db=database,
    )

    assert result["total"] == 23
    assert result["items"] == [session_metadata(session, device)]
    assert database.get.await_args.args == (Identity, identity_id)
    count_statement = str(database.scalar.await_args.args[0])
    page_statement = str(database.execute.await_args.args[0])
    assert "sessions.identity_id" in count_statement
    assert "sessions.identity_id" in page_statement
    assert "LIMIT" in page_statement and "OFFSET" in page_statement


@pytest.mark.asyncio
async def test_platform_sessions_returns_a_safe_empty_page_for_existing_identity():
    identity_id = uuid4()
    database = AsyncMock()
    database.get.return_value = SimpleNamespace(id=identity_id)
    database.scalar.return_value = 0
    database.execute.return_value = SimpleNamespace(all=lambda: [])

    result = await platform_sessions(
        identity_id=identity_id,
        limit=20,
        offset=0,
        access=(SimpleNamespace(identity_id=uuid4()), None, frozenset()),
        db=database,
    )

    assert result == {"total": 0, "items": []}


@pytest.mark.asyncio
async def test_platform_session_context_requires_a_persistent_active_grant():
    database = AsyncMock()
    database.get.return_value = PlatformGrant(identity_id=uuid4(), role="SUPER_ADMIN", active=True)
    assert await platform_context(database, uuid4()) == (
        PLATFORM_SESSION_CONTEXT,
        PLATFORM_SESSION_CONTEXT,
    )
    database.get.return_value.active = False
    assert await platform_context(database, uuid4()) is None


@pytest.mark.asyncio
async def test_platform_context_is_available_without_membership_data():
    database = AsyncMock()
    database.get.return_value = PlatformGrant(identity_id=uuid4(), role="SUPER_ADMIN", active=True)
    assert await platform_context(database, uuid4()) == (
        PLATFORM_SESSION_CONTEXT,
        PLATFORM_SESSION_CONTEXT,
    )


def test_local_email_is_allowed_only_in_local_development(monkeypatch):
    assert canonical_email("superadmin@globalchat.local") == "superadmin@globalchat.local"
    monkeypatch.setattr(
        "app.api.v1.password.get_settings", lambda: SimpleNamespace(app_env="production")
    )
    with pytest.raises(ValueError):
        canonical_email("superadmin@globalchat.local")
