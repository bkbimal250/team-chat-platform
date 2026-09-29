import asyncio
import json
from uuid import UUID, uuid4

from app.registry import Registry

MESSAGE_EVENTS = {
    "message.created.v1",
    "message.edited.v1",
    "message.deleted.v1",
    "message.reaction_added.v1",
    "message.reaction_removed.v1",
    "message.delivered.v1",
    "message.read.v1",
}
LIFECYCLE_EVENTS = {
    "conversation.member_removed.v1",
    "conversation.member_left.v1",
    "conversation.closed.v1",
}


class EventConsumer:
    def __init__(
        self,
        registry: Registry,
        instance_id: str = "local",
        remote_publish=None,
        claim_delivery=None,
    ):
        self.registry, self.processed, self.instance_id = registry, set(), instance_id
        self.remote_publish = remote_publish
        self.claim_delivery = claim_delivery

    async def process(self, event: dict) -> bool:
        event_id = UUID(event["event_id"])
        if event_id in self.processed:
            return False
        payload = event["payload"]
        organization_id = UUID(event["organization_id"])
        if event["event_type"] in LIFECYCLE_EVENTS:
            conversation_id = UUID(payload.get("conversation_id") or event["aggregate_id"])
            if event["event_type"] == "conversation.closed.v1":
                await self.registry.invalidate_conversation(organization_id, conversation_id)
            else:
                await self.registry.invalidate_member(
                    organization_id, UUID(payload["member_id"]), conversation_id
                )
            self.processed.add(event_id)
            return True
        if event["event_type"] == "realtime.delivery.v1":
            if payload["target_instance_id"] != self.instance_id:
                return False
            connection = self.registry.connections.get(payload["connection_id"])
            if not connection or connection.principal.organization_id != organization_id:
                return False
            if self.claim_delivery and not await self.claim_delivery(payload["delivery_id"]):
                self.processed.add(event_id)
                return True
            await self.registry.enqueue(connection, payload["event"])
            self.processed.add(event_id)
            return True
        if event["event_type"] not in MESSAGE_EVENTS:
            return False
        conversation_id = UUID(payload["conversation_id"])
        for connection in await self.registry.recipients(organization_id, conversation_id):
            delivery = {"version": 1, "type": event["event_type"], "payload": payload}
            target_instance = getattr(connection, "instance_id", self.instance_id)
            if target_instance == self.instance_id:
                await self.registry.enqueue(connection, delivery)
            elif self.remote_publish:
                await self.remote_publish(
                    {
                        "event_type": "realtime.delivery.v1",
                        "organization_id": str(organization_id),
                        "payload": {
                            "delivery_id": str(uuid4()),
                            "target_instance_id": target_instance,
                            "connection_id": connection.id,
                            "event": delivery,
                            "correlation_id": event.get("correlation_id", ""),
                        },
                    }
                )
        self.processed.add(event_id)
        return True


def rabbit_callback(consumer: EventConsumer, channel, method, _properties, body):
    try:
        asyncio.run(consumer.process(json.loads(body)))
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
