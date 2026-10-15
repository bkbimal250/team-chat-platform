from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.services.login_context import resolve_workspace_session_context


@pytest.mark.asyncio
async def test_personal_context_skips_organization_lookup(monkeypatch):
    memberships = AsyncMock(side_effect=AssertionError("must not call organization"))
    monkeypatch.setattr(
        "app.services.login_context.OrganizationServiceClient.memberships", memberships
    )
    assert await resolve_workspace_session_context(uuid4(), None, "c") == (None, None)
    memberships.assert_not_awaited()


@pytest.mark.asyncio
async def test_explicit_org_requires_single_active_membership(monkeypatch):
    org_id, member_id = uuid4(), uuid4()
    monkeypatch.setattr(
        "app.services.login_context.OrganizationServiceClient.memberships",
        AsyncMock(
            return_value=[
                SimpleNamespace(status="ACTIVE", organization_id=org_id, member_id=member_id)
            ]
        ),
    )
    assert await resolve_workspace_session_context(uuid4(), org_id, "c") == (org_id, member_id)


@pytest.mark.asyncio
async def test_unknown_org_is_rejected(monkeypatch):
    monkeypatch.setattr(
        "app.services.login_context.OrganizationServiceClient.memberships",
        AsyncMock(return_value=[]),
    )
    with pytest.raises(DomainError, match="MEMBERSHIP_INACTIVE"):
        await resolve_workspace_session_context(uuid4(), uuid4(), "c")
