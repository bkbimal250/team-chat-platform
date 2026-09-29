from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import main
from app.schemas import ReactionInput
from app.security import Principal


class HistoryDb:
    async def scalars(self, query):
        self.query = query
        return SimpleNamespace(
            all=lambda: [SimpleNamespace(sequence=1), SimpleNamespace(sequence=2)]
        )


class ReactionDb:
    def __init__(self, values):
        self.values = iter(values)
        self.added = []
        self.deleted = []

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def scalar(self, _):
        return next(self.values, None)

    def add(self, value):
        self.added.append(value)

    async def delete(self, value):
        self.deleted.append(value)


async def allow(*_):
    return SimpleNamespace()


@pytest.mark.asyncio
async def test_history_uses_sequence_cursor_order_and_limit(monkeypatch):
    monkeypatch.setattr(main, "authorize", allow)
    db = HistoryDb()
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    rows = await main.history(uuid4(), before_sequence=10, after_sequence=2, limit=500, p=p, db=db)
    sql = str(db.query)
    assert [row.sequence for row in rows] == [1, 2]
    assert "ORDER BY messages.sequence" in sql and "LIMIT" in sql


@pytest.mark.asyncio
async def test_reaction_add_duplicate_and_remove_are_member_scoped(monkeypatch):
    monkeypatch.setattr(main, "authorize", allow)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    message = SimpleNamespace(
        id=uuid4(),
        organization_id=p.organization_id,
        conversation_id=uuid4(),
        deleted_at=None,
        sender_user_id=uuid4(),
        sender_member_id=uuid4(),
        sender_device_id=uuid4(),
        type="TEXT",
        text="x",
        reply_to_message_id=None,
        client_message_id=uuid4(),
        sequence=1,
        created_at=datetime.now(UTC),
    )
    request = SimpleNamespace(headers={"X-Correlation-ID": "c"})
    db = ReactionDb([message, None])
    reaction = await main.add_reaction(
        message.id, ReactionInput(reaction="thumbs_up"), request, p, db
    )
    assert (
        reaction.member_id == p.member_id and db.added[-1].event_type == "message.reaction_added.v1"
    )
    duplicate = SimpleNamespace(member_id=p.member_id)
    assert (
        await main.add_reaction(
            message.id,
            ReactionInput(reaction="thumbs_up"),
            request,
            p,
            ReactionDb([message, duplicate]),
        )
        is duplicate
    )
    stored = SimpleNamespace(member_id=p.member_id)
    removed = ReactionDb([message, stored])
    assert await main.remove_reaction(message.id, "thumbs_up", request, p, removed) == {
        "status": "REMOVED"
    }
    assert (
        removed.deleted == [stored]
        and removed.added[-1].event_type == "message.reaction_removed.v1"
    )
