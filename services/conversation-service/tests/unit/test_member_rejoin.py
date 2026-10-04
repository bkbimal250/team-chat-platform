from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import services
from app.models import CType, MRole, MStatus


@pytest.mark.asyncio
async def test_rejoining_member_reuses_authoritative_membership_and_state(monkeypatch):
    actor, target = uuid4(), uuid4()
    conversation = SimpleNamespace(id=uuid4(), organization_id=uuid4(), type=CType.GROUP)
    owner = SimpleNamespace(status=MStatus.ACTIVE, role=MRole.OWNER)
    previous = SimpleNamespace(status=MStatus.REMOVED, role=MRole.ADMIN, left_at="old")
    service = services.ConversationService()

    async def mine(db, cid, mid):
        return owner if mid == actor else previous

    async def user(*args):
        return uuid4()

    emitted = []

    async def event(*args):
        emitted.append(args[1])

    monkeypatch.setattr(service, "mine", mine)
    monkeypatch.setattr(service, "member_user_id", user)
    monkeypatch.setattr(services, "event", event)

    class Db:
        async def execute(self, query):
            return SimpleNamespace(scalars=lambda: SimpleNamespace(all=lambda: [actor]))

        def add(self, row):
            raise AssertionError("Must reuse existing rows")

    assert await service.add(Db(), conversation, actor, [target], "rejoin") == [target]
    assert previous.status == MStatus.ACTIVE
    assert previous.role == MRole.MEMBER
    assert previous.left_at is None
    assert emitted == ["conversation.member_added.v1"]
