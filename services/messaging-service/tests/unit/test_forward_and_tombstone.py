from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.serialization import message_view
from app.services import send
from app.schemas import SendMessage


@pytest.mark.asyncio
async def test_forward_copies_source_content(monkeypatch):
    p = SimpleNamespace(
        user_id=uuid4(),
        member_id=uuid4(),
        device_id=uuid4(),
        organization_id=uuid4(),
    )
    source = SimpleNamespace(
        id=uuid4(),
        conversation_id=uuid4(),
        organization_id=p.organization_id,
        deleted_at=None,
        type="TEXT",
        text="original",
        attachment=None,
    )
    counter = SimpleNamespace(next_sequence=1)

    class Db:
        def __init__(self):
            self.added = []
            self.pending = [None, source, counter]

        async def scalar(self, query):
            if self.pending:
                return self.pending.pop(0)
            return None

        def add(self, value):
            self.added.append(value)

        async def flush(self):
            return None

    async def allow(*_args):
        return None

    monkeypatch.setattr("app.services.authorize", allow)
    message = await send(
        Db(),
        p,
        uuid4(),
        SendMessage(client_message_id=uuid4(), forward_from_message_id=source.id),
        "c",
    )
    assert message.forward_from_message_id == source.id
    assert message.text == "original"


def test_deleted_message_returns_tombstone():
    message = SimpleNamespace(
        id=uuid4(),
        organization_id=None,
        conversation_id=uuid4(),
        sender_member_id=uuid4(),
        sequence=3,
        status="DELETED",
        deleted_at=datetime.now(UTC),
        text="secret",
        attachment={"media_id": "x"},
    )
    view = message_view(message, [{"reaction": "ok"}])
    assert view["status"] == "DELETED"
    assert "text" not in view and "attachment" not in view
    assert view["reactions"] == [{"reaction": "ok"}]
