"""Fan-out encrypted sender-key distribution frames to conversation subscribers."""

import json
from uuid import uuid4


class E2eeDistributionBroadcaster:
    def __init__(self, registry, authorize):
        self.registry = registry
        self.authorize = authorize

    async def publish(self, connection, conversation_id, payload: dict):
        frame = {
            "version": 1,
            "type": "e2ee.sender_key_distribution.v1",
            "payload": {
                "conversation_id": str(conversation_id),
                "sender_user_id": str(connection.principal.user_id),
                "sender_device_id": str(connection.principal.device_id),
                **payload,
            },
        }
        org = connection.principal.organization_id
        sender_member = connection.principal.member_id
        metadata = self.registry.metadata_registry
        recipients = await (
            metadata.recipients(org, conversation_id)
            if metadata
            else self.registry.recipients(org, conversation_id)
        )
        for target in recipients:
            if target.principal.member_id == sender_member:
                continue
            try:
                await self.authorize(target.principal, conversation_id)
            except Exception:
                continue
            if target.instance_id == self.registry.instance_id:
                local = self.registry.connections.get(target.id)
                if local and conversation_id in local.subscriptions:
                    await self.registry.enqueue(local, frame)
            elif metadata:
                await metadata.redis.publish(
                    f"realtime:instance:{target.instance_id}:deliveries",
                    json.dumps(
                        {
                            "target_instance_id": target.instance_id,
                            "connection_id": target.id,
                            "organization_id": str(org) if org else None,
                            "delivery_id": str(uuid4()),
                            "event": frame,
                        }
                    ),
                )
