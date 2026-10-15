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
ORG_MEMBER_EVENTS = {
    "member.left.v2",
    "member.removed.v2",
    "member.reactivated.v2",
}


class EventConsumer:
    def __init__(
        self,
        registry: Registry,
        instance_id: str = "local",
        remote_publish=None,
        claim_delivery=None,
        on_workspace_revoke=None,
    ):
        self.registry, self.processed, self.instance_id = registry, set(), instance_id
        self.remote_publish = remote_publish
        self.claim_delivery = claim_delivery
        self.on_workspace_revoke = on_workspace_revoke

    async def _revoke_workspace(self, organization_id: UUID, member_id: UUID, status: str):
        revoke = getattr(self.registry, "revoke_workspace_member", None)
        if revoke:
            await revoke(organization_id, member_id, status)
        if self.on_workspace_revoke:
            await self.on_workspace_revoke(
                {
                    "organization_id": str(organization_id),
                    "member_id": str(member_id),
                    "status": status,
                }
            )

    async def _delivery_allowed(self, connection) -> bool:
        principal = connection.principal
        if principal.organization_id is None:
            return True
        store = getattr(self.registry, "membership_store", None)
        if store is None:
            return True
        return await store.is_active(principal.organization_id, principal.member_id)

    async def process(self, event: dict) -> bool:
        event_id = UUID(event["event_id"])
        if event_id in self.processed:
            return False
        payload = event["payload"]
        organization_id = UUID(event["organization_id"]) if event.get("organization_id") else None
        if event["event_type"] in ORG_MEMBER_EVENTS:
            member_id = UUID(str(payload["member_id"]))
            status = str(payload.get("status", event["event_type"].split(".")[1].upper())).upper()
            if event["event_type"] == "member.reactivated.v2":
                store = getattr(self.registry, "membership_store", None)
                if store:
                    await store.set_status(organization_id, member_id, "ACTIVE")
            else:
                await self._revoke_workspace(
                    organization_id,
                    member_id,
                    "LEFT" if event["event_type"] == "member.left.v2" else "REMOVED",
                )
            self.processed.add(event_id)
            return True
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
            if not await self._delivery_allowed(connection):
                self.processed.add(event_id)
                return True
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
            if not await self._delivery_allowed(connection):
                continue
            delivery = {"version": 1, "type": event["event_type"], "payload": payload}
            target_instance = getattr(connection, "instance_id", self.instance_id)
            if target_instance == self.instance_id and hasattr(connection, "queue"):
                await self.registry.enqueue(connection, delivery)
            elif self.remote_publish:
                await self.remote_publish(
                    {
                        "event_type": "realtime.delivery.v1",
                        "organization_id": str(organization_id) if organization_id else None,
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


def rabbit_callback(consumer: EventConsumer, channel, method, _properties, body, loop=None):
    try:
        work = consumer.process(json.loads(body))
        loop.run_until_complete(work) if loop else asyncio.run(work)
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
