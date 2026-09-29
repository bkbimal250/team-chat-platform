import asyncio
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.auth import Principal


@dataclass
class Connection:
    id: str
    principal: Principal
    queue: asyncio.Queue
    subscriptions: set[UUID] = field(default_factory=set)
    connected_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    instance_id: str = "local"


@dataclass
class RemoteConnection:
    """Serializable routing record reconstructed from Redis metadata."""

    id: str
    principal: Principal
    instance_id: str


class Registry:
    """Local socket registry, optionally mirrored to shared Redis metadata."""

    def __init__(self, max_queue: int = 100, metadata_registry=None, instance_id: str = "local"):
        self.max_queue, self.connections = max_queue, {}
        self.metadata_registry, self.instance_id = metadata_registry, instance_id
        self.typing = {}

    async def register(self, principal: Principal) -> Connection:
        for existing in list(self.connections.values()):
            if (
                existing.principal.session_id == principal.session_id
                and existing.principal.device_id == principal.device_id
            ):
                await self.remove(existing.id)
        connection = Connection(
            str(uuid4()), principal, asyncio.Queue(self.max_queue), instance_id=self.instance_id
        )
        self.connections[connection.id] = connection
        if self.metadata_registry:
            await self.metadata_registry.register(connection)
        return connection

    async def refresh(self, connection: Connection):
        if self.metadata_registry:
            await self.metadata_registry.refresh(connection.id)

    async def remove(self, connection_id: str):
        connection = self.connections.pop(connection_id, None)
        if connection:
            self.typing = {
                k: v for k, v in self.typing.items() if k[2] != connection.principal.member_id
            }
            if self.metadata_registry:
                await self.metadata_registry.remove(connection.id)

    async def subscribe(self, connection: Connection, conversation_id: UUID):
        connection.subscriptions.add(conversation_id)
        if self.metadata_registry:
            await self.metadata_registry.subscribe(connection, conversation_id)

    async def unsubscribe(self, connection: Connection, conversation_id: UUID):
        connection.subscriptions.discard(conversation_id)
        if self.metadata_registry:
            await self.metadata_registry.unsubscribe(connection, conversation_id)

    async def recipients(self, organization_id: UUID, conversation_id: UUID):
        return [
            c
            for c in self.connections.values()
            if c.principal.organization_id == organization_id and conversation_id in c.subscriptions
        ]

    async def enqueue(self, connection: Connection, payload: dict) -> bool:
        if connection.queue.full():
            return False
        connection.queue.put_nowait(payload)
        return True

    async def online_for_identity(self, identity_id: UUID):
        return any(c.principal.identity_id == identity_id for c in self.connections.values())

    async def set_typing(self, connection: Connection, conversation_id: UUID, active: bool):
        key = (
            connection.principal.organization_id,
            conversation_id,
            connection.principal.member_id,
        )
        if active:
            self.typing[key] = datetime.now(UTC)
        else:
            self.typing.pop(key, None)

    async def invalidate_member(
        self, organization_id: UUID, member_id: UUID, conversation_id: UUID
    ):
        for connection in self.connections.values():
            if (
                connection.principal.organization_id == organization_id
                and connection.principal.member_id == member_id
            ):
                connection.subscriptions.discard(conversation_id)
        self.typing.pop((organization_id, conversation_id, member_id), None)

    async def invalidate_conversation(self, organization_id: UUID, conversation_id: UUID):
        for connection in self.connections.values():
            if connection.principal.organization_id == organization_id:
                connection.subscriptions.discard(conversation_id)
        self.typing = {
            k: v for k, v in self.typing.items() if k[:2] != (organization_id, conversation_id)
        }


class RedisMetadataRegistry:
    """Shared, serializable routing metadata. WebSocket objects never leave the owner process."""

    def __init__(self, redis, instance_id: str):
        self.redis, self.instance_id = redis, instance_id

    @staticmethod
    def _connection_key(connection_id: str) -> str:
        return f"realtime:connection:{connection_id}"

    @staticmethod
    def _subscription_key(connection_id: str) -> str:
        return f"realtime:connection:{connection_id}:subscriptions"

    @staticmethod
    def _organization_key(organization_id: UUID | str) -> str:
        return f"realtime:organization:{organization_id}:connections"

    @staticmethod
    def _instance_key(instance_id: str) -> str:
        return f"realtime:instance:{instance_id}"

    async def register(self, connection: Connection, ttl: int = 90):
        key = self._connection_key(connection.id)
        organization_id = connection.principal.organization_id
        await self.redis.hset(
            key,
            mapping={
                "organization_id": str(organization_id),
                "identity_id": str(connection.principal.identity_id),
                "member_id": str(connection.principal.member_id),
                "session_id": str(connection.principal.session_id),
                "device_id": str(connection.principal.device_id),
                "instance_id": self.instance_id,
            },
        )
        await self.redis.expire(key, ttl)
        await self.redis.sadd(self._instance_key(self.instance_id), connection.id)
        await self.redis.expire(self._instance_key(self.instance_id), ttl)
        await self.redis.sadd(self._organization_key(organization_id), connection.id)
        await self.redis.expire(self._organization_key(organization_id), ttl)
        return key

    async def refresh(self, connection_id: str, ttl: int = 90):
        data = await self._data(connection_id) if hasattr(self.redis, "hgetall") else {}
        await self.redis.expire(self._connection_key(connection_id), ttl)
        if data:
            await self.redis.expire(self._instance_key(data["instance_id"]), ttl)
            await self.redis.expire(self._organization_key(data["organization_id"]), ttl)
            await self.redis.expire(self._subscription_key(connection_id), ttl)

    async def _data(self, connection_id: str) -> dict[str, str]:
        data = await self.redis.hgetall(self._connection_key(connection_id))
        return {
            (k.decode() if isinstance(k, bytes) else k): (v.decode() if isinstance(v, bytes) else v)
            for k, v in data.items()
        }

    async def remove_instance(self):
        ids = await self.redis.smembers(self._instance_key(self.instance_id))
        for connection_id in ids:
            await self.remove(
                connection_id.decode() if isinstance(connection_id, bytes) else connection_id
            )
        await self.redis.delete(self._instance_key(self.instance_id))

    async def get_connection(self, connection_id: str, organization_id: UUID):
        data = await self._data(connection_id) if hasattr(self.redis, "hgetall") else {}
        if not data or data.get("organization_id") != str(organization_id):
            return None
        required = {
            "instance_id",
            "organization_id",
            "identity_id",
            "member_id",
            "session_id",
            "device_id",
        }
        return {"connection_id": connection_id, **data} if required <= data.keys() else None

    async def get_instance_connections(self, instance_id: str, organization_id: UUID):
        result = []
        for raw in await self.redis.smembers(self._instance_key(instance_id)):
            connection_id = raw.decode() if isinstance(raw, bytes) else raw
            record = await self.get_connection(connection_id, organization_id)
            if record:
                result.append(record)
            else:
                await self.redis.srem(self._instance_key(instance_id), connection_id)
        return result

    async def get_organization_connections(self, organization_id: UUID):
        result = []
        key = self._organization_key(organization_id)
        for raw in await self.redis.smembers(key):
            connection_id = raw.decode() if isinstance(raw, bytes) else raw
            record = await self.get_connection(connection_id, organization_id)
            if record:
                result.append(record)
            else:
                await self.redis.srem(key, connection_id)
        return result

    async def subscribe(self, connection: Connection, conversation_id: UUID, ttl: int = 90):
        key = self._subscription_key(connection.id)
        await self.redis.sadd(key, str(conversation_id))
        await self.redis.expire(key, ttl)

    async def unsubscribe(self, connection: Connection, conversation_id: UUID):
        await self.redis.srem(self._subscription_key(connection.id), str(conversation_id))

    async def recipients(self, organization_id: UUID, conversation_id: UUID):
        recipients = []
        for record in await self.get_organization_connections(organization_id):
            if await self.redis.sismember(
                self._subscription_key(record["connection_id"]), str(conversation_id)
            ):
                recipients.append(
                    RemoteConnection(
                        id=record["connection_id"],
                        principal=Principal(
                            UUID(record["identity_id"]),
                            UUID(record["session_id"]),
                            UUID(record["device_id"]),
                            UUID(record["organization_id"]),
                            UUID(record["member_id"]),
                        ),
                        instance_id=record["instance_id"],
                    )
                )
        return recipients

    async def invalidate_member(
        self, organization_id: UUID, member_id: UUID, conversation_id: UUID
    ):
        for record in await self.get_organization_connections(organization_id):
            if record["member_id"] == str(member_id):
                await self.redis.srem(
                    self._subscription_key(record["connection_id"]), str(conversation_id)
                )

    async def invalidate_conversation(self, organization_id: UUID, conversation_id: UUID):
        for record in await self.get_organization_connections(organization_id):
            await self.redis.srem(
                self._subscription_key(record["connection_id"]), str(conversation_id)
            )

    async def claim_delivery(self, delivery_id: str, ttl: int = 300) -> bool:
        return bool(await self.redis.set(f"realtime:delivery:{delivery_id}", "1", nx=True, ex=ttl))

    async def remove(self, connection_id: str):
        data = await self._data(connection_id) if hasattr(self.redis, "hgetall") else {}
        await self.redis.delete(
            self._connection_key(connection_id), self._subscription_key(connection_id)
        )
        if data:
            await self.redis.srem(self._instance_key(data["instance_id"]), connection_id)
            await self.redis.srem(self._organization_key(data["organization_id"]), connection_id)
