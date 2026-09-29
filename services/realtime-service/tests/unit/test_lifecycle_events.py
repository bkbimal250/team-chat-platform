from uuid import uuid4

import pytest

from app.auth import Principal
from app.events import EventConsumer
from app.registry import Registry


async def registered(registry, org):
    return await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event_type", ["conversation.member_removed.v1", "conversation.member_left.v1"]
)
async def test_member_lifecycle_events_remove_subscription_and_typing(event_type):
    registry = Registry()
    org, conversation = uuid4(), uuid4()
    connection = await registered(registry, org)
    await registry.subscribe(connection, conversation)
    await registry.set_typing(connection, conversation, True)
    event = {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "organization_id": str(org),
        "aggregate_id": str(conversation),
        "payload": {"member_id": str(connection.principal.member_id)},
    }

    assert await EventConsumer(registry).process(event)
    assert conversation not in connection.subscriptions
    assert registry.typing == {}


@pytest.mark.asyncio
async def test_conversation_closed_removes_all_members_but_preserves_other_conversations():
    registry = Registry()
    org, conversation, other = uuid4(), uuid4(), uuid4()
    first, second = await registered(registry, org), await registered(registry, org)
    for connection in (first, second):
        await registry.subscribe(connection, conversation)
        await registry.subscribe(connection, other)
        await registry.set_typing(connection, conversation, True)
        await registry.set_typing(connection, other, True)
    event = {
        "event_id": str(uuid4()),
        "event_type": "conversation.closed.v1",
        "organization_id": str(org),
        "aggregate_id": str(conversation),
        "payload": {},
    }

    assert await EventConsumer(registry).process(event)
    for connection in (first, second):
        assert conversation not in connection.subscriptions
        assert other in connection.subscriptions
    assert all(key[1] == other for key in registry.typing)
