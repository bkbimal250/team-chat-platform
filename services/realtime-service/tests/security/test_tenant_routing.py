from uuid import uuid4

import pytest

from app.auth import Principal
from app.events import EventConsumer
from app.registry import Registry


@pytest.mark.asyncio
async def test_cross_tenant_event_delivery_is_prevented():
    registry = Registry()
    c = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    conversation = uuid4()
    await registry.subscribe(c, conversation)
    event = {
        "event_id": str(uuid4()),
        "event_type": "message.created.v1",
        "organization_id": str(uuid4()),
        "payload": {"conversation_id": str(conversation)},
    }
    assert await EventConsumer(registry).process(event) and c.queue.empty()
