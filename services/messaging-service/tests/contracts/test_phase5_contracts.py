import json
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.events import Publisher, apply_projection
from app.services import event


class Db:
    def __init__(self):
        self.added = []

    async def scalar(self, _):
        return None

    def add(self, value):
        self.added.append(value)

    async def delete(self, _):
        return None


def envelope(event_type, payload):
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "conversation-service",
        "organization_id": str(uuid4()),
        "aggregate_id": str(uuid4()),
        "correlation_id": "c",
        "payload": payload,
    }


@pytest.mark.asyncio
async def test_created_contract_bootstraps_projections():
    db = Db()
    member = {"member_id": str(uuid4()), "user_id": str(uuid4()), "status": "ACTIVE"}
    assert await apply_projection(
        db, envelope("conversation.created.v1", {"type": "DIRECT", "members": [member]})
    )
    assert len(db.added) == 3 and db.added[0].type == "DIRECT"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type",
    [
        "conversation.updated.v1",
        "conversation.closed.v1",
        "conversation.member_added.v1",
        "conversation.member_removed.v1",
        "conversation.member_left.v1",
        "conversation.member_role_changed.v1",
        "conversation.ownership_transferred.v1",
    ],
)
async def test_consumed_conversation_contracts(event_type):
    assert await apply_projection(
        Db(), envelope(event_type, {"conversation_id": str(uuid4()), "member_id": str(uuid4())})
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("event_type", ["user.blocked.v1", "user.unblocked.v1"])
async def test_consumed_block_contracts(event_type):
    assert await apply_projection(
        Db(),
        envelope(event_type, {"blocker_user_id": str(uuid4()), "blocked_user_id": str(uuid4())}),
    )


@pytest.mark.asyncio
async def test_malformed_consumed_event_is_rejected():
    with pytest.raises(KeyError):
        await apply_projection(Db(), envelope("conversation.created.v1", {}))


@pytest.mark.parametrize(
    "event_type",
    [
        "message.created.v1",
        "message.edited.v1",
        "message.deleted.v1",
        "message.reaction_added.v1",
        "message.reaction_removed.v1",
        "message.delivered.v1",
        "message.read.v1",
    ],
)
def test_published_message_contracts(event_type):
    message = SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        conversation_id=uuid4(),
        sender_user_id=uuid4(),
        sender_member_id=uuid4(),
        sender_device_id=uuid4(),
        type="TEXT",
        text="hello",
        reply_to_message_id=None,
        client_message_id=uuid4(),
        sequence=3,
        created_at=datetime.now(UTC),
    )
    outbox = event(message, event_type, "correlation")
    outbox.created_at = datetime.now(UTC)
    publisher = Publisher.__new__(Publisher)
    captured = {}
    publisher.channel = SimpleNamespace(basic_publish=lambda **kwargs: captured.update(kwargs))
    publisher.publish(outbox)
    wire = json.loads(captured["body"])
    assert {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "producer",
        "organization_id",
        "aggregate_id",
        "correlation_id",
        "payload",
    } <= wire.keys()
    assert wire["event_type"] == event_type
    assert {
        "message_id",
        "organization_id",
        "conversation_id",
        "sender_user_id",
        "sender_member_id",
        "sender_device_id",
        "type",
        "text",
        "reply_to_message_id",
        "client_message_id",
        "sequence",
        "created_at",
    } <= wire["payload"].keys()
