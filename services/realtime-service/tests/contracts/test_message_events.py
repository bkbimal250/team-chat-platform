from uuid import uuid4

import pytest

from app.auth import Principal
from app.events import EventConsumer
from app.registry import Registry


@pytest.mark.asyncio
async def test_message_event_fanout_has_idempotency_and_tenant_routing():
    registry = Registry()
    org, conversation = uuid4(), uuid4()
    recipient = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    await registry.subscribe(recipient, conversation)
    consumer = EventConsumer(registry)
    event = {
        "event_id": str(uuid4()),
        "event_type": "message.created.v1",
        "organization_id": str(org),
        "payload": {"conversation_id": str(conversation), "message_id": str(uuid4())},
    }
    assert await consumer.process(event) and recipient.queue.qsize() == 1
    assert not await consumer.process(event) and recipient.queue.qsize() == 1


@pytest.mark.asyncio
async def test_remote_recipient_is_published_as_terminal_delivery():
    registry = Registry()
    org, conversation = uuid4(), uuid4()
    recipient = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    recipient.instance_id = "instance-b"
    await registry.subscribe(recipient, conversation)
    published = []

    async def remote_publish(envelope):
        published.append(envelope)

    event = {
        "event_id": str(uuid4()),
        "event_type": "message.created.v1",
        "organization_id": str(org),
        "correlation_id": "correlation-123",
        "payload": {"conversation_id": str(conversation), "message_id": str(uuid4())},
    }
    assert await EventConsumer(registry, "instance-a", remote_publish).process(event)

    assert recipient.queue.qsize() == 0
    assert len(published) == 1
    envelope = published[0]
    assert envelope["event_type"] == "realtime.delivery.v1"
    assert envelope["organization_id"] == str(org)
    assert envelope["payload"]["delivery_id"]
    assert envelope["payload"]["target_instance_id"] == "instance-b"
    assert envelope["payload"]["connection_id"] == recipient.id
    assert envelope["payload"]["event"]["payload"] == event["payload"]
    assert envelope["payload"]["correlation_id"] == "correlation-123"


@pytest.mark.asyncio
async def test_terminal_delivery_claims_once_and_never_republishes():
    registry = Registry()
    org = uuid4()
    recipient = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    claimed, published = set(), []

    async def claim_delivery(delivery_id):
        if delivery_id in claimed:
            return False
        claimed.add(delivery_id)
        return True

    async def remote_publish(envelope):
        published.append(envelope)

    consumer = EventConsumer(registry, "instance-b", remote_publish, claim_delivery)
    delivery = {
        "delivery_id": "delivery-123",
        "target_instance_id": "instance-b",
        "connection_id": recipient.id,
        "event": {"version": 1, "type": "message.created.v1", "payload": {"body": "hello"}},
    }
    event = {
        "event_id": str(uuid4()),
        "event_type": "realtime.delivery.v1",
        "organization_id": str(org),
        "payload": delivery,
    }
    assert await consumer.process(event)
    duplicate = {**event, "event_id": str(uuid4())}
    assert await consumer.process(duplicate)

    assert recipient.queue.qsize() == 1
    assert published == []


@pytest.mark.asyncio
async def test_terminal_delivery_for_another_instance_does_not_claim_or_enqueue():
    registry = Registry()
    org = uuid4()
    recipient = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    claims = []

    async def claim_delivery(delivery_id):
        claims.append(delivery_id)
        return True

    event = {
        "event_id": str(uuid4()),
        "event_type": "realtime.delivery.v1",
        "organization_id": str(org),
        "payload": {
            "delivery_id": "delivery-123",
            "target_instance_id": "another-instance",
            "connection_id": recipient.id,
            "event": {"version": 1, "type": "message.created.v1", "payload": {}},
        },
    }
    assert not await EventConsumer(registry, "instance-b", claim_delivery=claim_delivery).process(
        event
    )
    assert recipient.queue.qsize() == 0
    assert claims == []
