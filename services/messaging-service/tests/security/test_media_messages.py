from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import DomainError
from app.events import apply_projection
from app.models import MediaProjection
from app.schemas import SendMessage
from app.services import media_attachment


class Db:
    def __init__(self, row=None):
        self.row, self.added = row, []

    async def get(self, model, key):
        return self.row

    async def scalar(self, query):
        return None

    def add(self, row):
        self.added.append(row)


def fixture():
    p = SimpleNamespace(organization_id=uuid4(), member_id=uuid4())
    cid = uuid4()
    row = MediaProjection(
        id=uuid4(),
        organization_id=p.organization_id,
        conversation_id=cid,
        uploader_member_id=p.member_id,
        status="READY",
        metadata_json={
            "media_type": "audio",
            "mime_type": "audio/webm",
            "filename": "voice.webm",
            "size_bytes": 100,
        },
    )
    body = SendMessage(client_message_id=uuid4(), type="VOICE", media_id=row.id)
    return p, cid, row, body


@pytest.mark.asyncio
async def test_verified_attachment_metadata_is_server_owned():
    p, cid, row, body = fixture()
    result = await media_attachment(Db(row), p, cid, body)
    assert result == {"media_id": str(row.id), **row.metadata_json}
    assert "object_key" not in result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "field", ["organization_id", "conversation_id", "uploader_member_id", "status", "type"]
)
async def test_media_reference_fail_closed(field):
    p, cid, row, body = fixture()
    if field == "status":
        row.status = "DELETED"
    elif field == "type":
        body.type = "VIDEO"
    else:
        setattr(row, field, uuid4())
    with pytest.raises(DomainError):
        await media_attachment(Db(row), p, cid, body)


@pytest.mark.asyncio
async def test_deleted_projection_cannot_be_revived_by_late_ready_event():
    p, cid, row, body = fixture()
    row.status = "DELETED"
    db = Db(row)
    envelope = {
        "event_id": str(uuid4()),
        "organization_id": str(p.organization_id),
        "producer": "media-service",
        "event_type": "media.ready.v1",
        "payload": {
            "media_id": str(row.id),
            "conversation_id": str(cid),
            "uploader_member_id": str(p.member_id),
            **row.metadata_json,
        },
    }
    await apply_projection(db, envelope)
    assert row.status == "DELETED"


@pytest.mark.parametrize("kind", ["IMAGE", "VIDEO", "AUDIO", "VOICE", "DOCUMENT"])
def test_media_request_requires_reference(kind):
    with pytest.raises(ValueError):
        SendMessage(client_message_id=uuid4(), type=kind)


@pytest.mark.asyncio
async def test_media_send_emits_reference_only_after_authorization():
    from datetime import UTC, datetime

    from app.models import ConversationSequence, Message, OutboxEvent
    from app.services import send

    p, cid, row, body = fixture()
    p.user_id, p.device_id = uuid4(), uuid4()

    class SendDb(Db):
        def __init__(self):
            super().__init__(row)
            self.results = iter(
                [
                    SimpleNamespace(status="ACTIVE"),
                    SimpleNamespace(status="ACTIVE", type="GROUP"),
                    SimpleNamespace(status="ACTIVE"),
                    None,
                    ConversationSequence(conversation_id=cid, next_sequence=1),
                ]
            )

        async def scalar(self, query):
            return next(self.results)

        async def flush(self):
            for item in self.added:
                if isinstance(item, Message):
                    item.id, item.created_at = uuid4(), datetime.now(UTC)

    db = SendDb()
    message = await send(db, p, cid, body, "trace")
    assert message.type == "VOICE" and message.attachment["media_id"] == str(row.id)
    event = next(item for item in db.added if isinstance(item, OutboxEvent))
    assert event.payload["media_id"] == str(row.id)
    assert event.payload["attachment"] == message.attachment
