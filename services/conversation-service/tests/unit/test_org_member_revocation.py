from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import events
from app.models import CStatus, CType, MStatus


@pytest.mark.asyncio
async def test_member_removed_revokes_workspace_conversations_only(monkeypatch):
    org, member_id, personal_cid = uuid4(), uuid4(), uuid4()
    workspace_member = SimpleNamespace(
        status=MStatus.ACTIVE,
        left_at=None,
        member_id=member_id,
        user_id=uuid4(),
        role="MEMBER",
    )
    workspace_conv = SimpleNamespace(
        id=uuid4(),
        organization_id=org,
        type=CType.GROUP,
        status=CStatus.ACTIVE,
        created_at=None,
        updated_at=None,
        closed_at=None,
        deleted_at=None,
    )
    revoked = []

    async def revoke(self, db, organization_id, mid, status, correlation):
        assert organization_id == org and mid == member_id
        revoked.append(status)

    monkeypatch.setattr(events.ConversationService, "revoke_org_conversations", revoke)

    class Session:
        def __init__(self):
            self.added = []

        async def scalar(self, query):
            if "processed_events" in str(query).lower():
                return None
            return None

        def add(self, row):
            self.added.append(row)

    event = {
        "event_id": str(uuid4()),
        "event_type": "member.removed.v2",
        "organization_id": str(org),
        "correlation_id": "corr",
        "producer": "organization-service",
        "payload": {
            "member_id": str(member_id),
            "user_id": str(uuid4()),
            "status": "REMOVED",
        },
    }
    session = Session()
    await events.consume(session, event)
    assert revoked == [MStatus.REMOVED]
    assert any(getattr(row, "status", None) == "REMOVED" for row in session.added)


@pytest.mark.asyncio
async def test_member_reactivated_updates_projection_without_revoke(monkeypatch):
    org, member_id = uuid4(), uuid4()
    revoke_called = False

    async def revoke(*_):
        nonlocal revoke_called
        revoke_called = True

    monkeypatch.setattr(events.ConversationService, "revoke_org_conversations", revoke)

    projection = SimpleNamespace(status="REMOVED", user_id=None)

    class Session:
        def __init__(self):
            self.added = []

        async def scalar(self, query):
            q = str(query).lower()
            if "processed_events" in q:
                return None
            if "member_projections" in q:
                return projection
            return None

        def add(self, row):
            self.added.append(row)

    event = {
        "event_id": str(uuid4()),
        "event_type": "member.reactivated.v2",
        "organization_id": str(org),
        "correlation_id": "corr",
        "producer": "organization-service",
        "payload": {
            "member_id": str(member_id),
            "user_id": str(uuid4()),
            "status": "ACTIVE",
        },
    }
    await events.consume(Session(), event)
    assert projection.status == "ACTIVE"
    assert not revoke_called
