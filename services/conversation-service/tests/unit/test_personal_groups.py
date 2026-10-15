from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import DomainError
from app.models import MStatus
from app.schemas import GroupIn
from app.services import ConversationService


@pytest.mark.asyncio
async def test_personal_group_resolves_contacts_and_blocks(monkeypatch):
    actor, contact, peer = uuid4(), uuid4(), uuid4()
    service = ConversationService()

    async def resolve(actor_id, contact_id):
        assert actor_id == actor and contact_id == contact
        return peer

    async def blocked(db, left, right):
        return left == actor and right == peer

    monkeypatch.setattr("app.services.resolve_contact_identity", resolve)
    monkeypatch.setattr("app.services.blocked_between", blocked)

    with pytest.raises(DomainError) as error:
        await service.personal_group(
            SimpleNamespace(),
            actor,
            GroupIn(title="Friends", member_ids=[contact]),
            "test",
        )
    assert error.value.code == "DIRECT_CONVERSATION_BLOCKED"


@pytest.mark.asyncio
async def test_revoke_org_conversations_skips_personal_rows(monkeypatch):
    org, member_id = uuid4(), uuid4()
    emitted = []

    async def event(db, typ, conversation, correlation, fields=[], member=None, **_):
        emitted.append((typ, conversation.organization_id))

    monkeypatch.setattr("app.services.event", event)

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
        type="GROUP",
        status="ACTIVE",
        created_at=None,
        updated_at=None,
        closed_at=None,
        deleted_at=None,
    )

    class Result:
        def all(self):
            return [(workspace_member, workspace_conv)]

    class Session:
        async def execute(self, query):
            assert "organization_id" in str(query)
            return Result()

    await ConversationService().revoke_org_conversations(
        Session(), org, member_id, MStatus.REMOVED, "corr"
    )
    assert workspace_member.status == MStatus.REMOVED
    assert emitted and emitted[0][1] == org
