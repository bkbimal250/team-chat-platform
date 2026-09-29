from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import services
from app.core import DomainError
from app.schemas import SendMessage
from app.security import Principal


class Db:
    def __init__(self, values):
        self.values = iter(values)
        self.added = []
        self.flushed = 0

    async def scalar(self, _):
        return next(self.values, None)

    def add(self, value):
        self.added.append(value)

    async def flush(self):
        self.flushed += 1


async def allow(*_):
    return SimpleNamespace()


@pytest.mark.asyncio
async def test_send_uses_trusted_principal_and_allocates_sequence(monkeypatch):
    monkeypatch.setattr(services, "authorize", allow)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    counter = SimpleNamespace(next_sequence=4)
    db = Db([None, counter])
    message = await services.send(
        db, p, uuid4(), SendMessage(client_message_id=uuid4(), text="hello"), "c"
    )
    assert message.sender_user_id == p.user_id and message.sender_member_id == p.member_id
    assert message.sender_device_id == p.device_id and message.sequence == 4
    assert counter.next_sequence == 5


@pytest.mark.asyncio
async def test_duplicate_client_message_returns_existing_logical_message(monkeypatch):
    monkeypatch.setattr(services, "authorize", allow)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    existing = SimpleNamespace(id=uuid4())
    assert (
        await services.send(
            Db([existing]), p, uuid4(), SendMessage(client_message_id=uuid4(), text="retry"), "c"
        )
        is existing
    )


@pytest.mark.asyncio
async def test_cross_conversation_reply_is_rejected(monkeypatch):
    monkeypatch.setattr(services, "authorize", allow)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    with pytest.raises(DomainError, match="Reply target"):
        await services.send(
            Db([None, None]),
            p,
            uuid4(),
            SendMessage(client_message_id=uuid4(), text="reply", reply_to_message_id=uuid4()),
            "c",
        )


@pytest.mark.asyncio
async def test_delivery_and_read_high_water_marks_are_monotonic(monkeypatch):
    monkeypatch.setattr(services, "authorize", allow)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    state = SimpleNamespace(last_delivered_sequence=5, last_read_sequence=3)
    db = Db([state, state, state])
    await services.mark(db, p, uuid4(), 4, False, "c")
    await services.mark(db, p, uuid4(), 5, True, "c")
    assert state.last_delivered_sequence == 5 and state.last_read_sequence == 5
    with pytest.raises(DomainError, match="Read cannot exceed"):
        await services.mark(db, p, uuid4(), 6, True, "c")
