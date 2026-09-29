from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import DomainError
from app.events import apply_projection
from app.security import Principal
from app.services import authorize


class ProjectionDb:
    def __init__(self, results=()):
        self.results = iter(results)
        self.added = []
        self.deleted = []

    async def scalar(self, _):
        return next(self.results, None)

    def add(self, value):
        self.added.append(value)

    async def delete(self, value):
        self.deleted.append(value)


def block_event(kind, blocker, blocked, organization):
    return {
        "event_id": str(uuid4()),
        "event_type": kind,
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "user-service",
        "organization_id": str(organization),
        "aggregate_id": str(uuid4()),
        "correlation_id": "c",
        "payload": {"blocker_user_id": str(blocker), "blocked_user_id": str(blocked)},
    }


class AuthDb:
    def __init__(self, conversation, member, block):
        self.values = iter([conversation, member, block])
        self.peers = []

    async def scalar(self, _):
        return next(self.values)

    async def scalars(self, _):
        return SimpleNamespace(all=lambda: self.peers)


@pytest.mark.asyncio
async def test_block_and_unblock_events_restore_bidirectional_direct_authorization():
    a, b, org, conversation_id = uuid4(), uuid4(), uuid4(), uuid4()
    db = ProjectionDb()
    assert await apply_projection(db, block_event("user.blocked.v1", a, b, org))
    block = db.added[0]
    conversation = SimpleNamespace(status="ACTIVE", type="DIRECT")
    member = SimpleNamespace(status="ACTIVE")
    auth = AuthDb(conversation, member, block)
    auth.peers = [SimpleNamespace(user_id=a), SimpleNamespace(user_id=b)]
    with pytest.raises(DomainError, match="DIRECT_CONVERSATION_BLOCKED"):
        await authorize(auth, Principal(a, uuid4(), uuid4(), org), conversation_id)
    unblock = ProjectionDb([None, block])
    assert await apply_projection(unblock, block_event("user.unblocked.v1", a, b, org))
    assert unblock.deleted == [block]
    allowed = AuthDb(conversation, member, None)
    allowed.peers = [SimpleNamespace(user_id=a), SimpleNamespace(user_id=b)]
    assert (
        await authorize(allowed, Principal(b, uuid4(), uuid4(), org), conversation_id)
        is conversation
    )
