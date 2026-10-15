"""Ephemeral participant-only typing fanout using existing Redis instance delivery."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from uuid import uuid4


class TypingBroadcaster:
    def __init__(self, registry, authorize, ttl=5):
        self.registry, self.authorize, self.ttl = registry, authorize, ttl
        self.tasks = {}

    async def broadcast(self, connection, conversation_id, active):
        org, member = connection.principal.organization_id, connection.principal.member_id
        frame = {
            "version": 1,
            "type": "typing.updated.v1",
            "payload": {
                "conversation_id": str(conversation_id),
                "member_id": str(member),
                "active": active,
                "expires_at": (datetime.now(UTC) + timedelta(seconds=self.ttl)).isoformat(),
            },
        }
        metadata = self.registry.metadata_registry
        recipients = await (
            metadata.recipients(org, conversation_id)
            if metadata
            else self.registry.recipients(org, conversation_id)
        )
        for target in recipients:
            if target.principal.organization_id != org or target.principal.member_id == member:
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

    async def update(self, connection, conversation_id, active):
        key = (connection.id, conversation_id)
        previous = self.tasks.pop(key, None)
        if previous:
            previous.cancel()
        await self.registry.set_typing(connection, conversation_id, active)
        await self.broadcast(connection, conversation_id, active)
        if active:

            async def expire():
                try:
                    await asyncio.sleep(self.ttl)
                    await self.registry.set_typing(connection, conversation_id, False)
                    await self.broadcast(connection, conversation_id, False)
                finally:
                    if self.tasks.get(key) is asyncio.current_task():
                        self.tasks.pop(key, None)

            self.tasks[key] = asyncio.create_task(expire())

    async def remove(self, connection):
        for key in list(self.tasks):
            if key[0] == connection.id:
                self.tasks.pop(key).cancel()
                await self.registry.set_typing(connection, key[1], False)
                await self.broadcast(connection, key[1], False)

    async def close(self):
        tasks = list(self.tasks.values())
        self.tasks.clear()
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
