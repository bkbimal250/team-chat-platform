from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.main import delete, edit
from app.schemas import EditMessage
from app.security import Principal


class Db:
    def __init__(self, value):
        self.value = value
        self.added = []

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def scalar(self, _):
        return self.value

    def add(self, value):
        self.added.append(value)


def request():
    return SimpleNamespace(headers={"X-Correlation-ID": "c"})


def message(principal):
    return SimpleNamespace(
        id=uuid4(),
        organization_id=principal.organization_id,
        sender_member_id=principal.member_id,
        type="TEXT",
        deleted_at=None,
        text="old",
        sequence=7,
        edited_at=None,
        created_at=datetime.now(UTC),
        conversation_id=uuid4(),
        sender_user_id=principal.user_id,
        sender_device_id=principal.device_id,
        reply_to_message_id=None,
        client_message_id=uuid4(),
        status="ACTIVE",
    )


@pytest.mark.asyncio
async def test_sender_edit_and_soft_delete_preserve_message_row_and_sequence():
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    m = message(p)
    db = Db(m)
    await edit(m.id, EditMessage(text="new"), request(), p, db)
    assert (
        m.text == "new"
        and m.edited_at is not None
        and db.added[-1].event_type == "message.edited.v1"
    )
    await delete(m.id, request(), p, db)
    assert m.deleted_at is not None and m.sequence == 7 and m.text is None
    assert db.added[-1].event_type == "message.deleted.v1"


@pytest.mark.asyncio
async def test_other_member_cannot_edit_or_delete():
    owner = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    other = Principal(uuid4(), uuid4(), uuid4(), owner.organization_id)
    m = message(owner)
    from app.core import DomainError

    with pytest.raises(DomainError):
        await edit(m.id, EditMessage(text="x"), request(), other, Db(m))
    with pytest.raises(DomainError):
        await delete(m.id, request(), other, Db(m))
