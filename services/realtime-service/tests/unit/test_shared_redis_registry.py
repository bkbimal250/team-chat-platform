from collections import defaultdict
from uuid import uuid4

import pytest

from app.auth import Principal
from app.registry import RedisMetadataRegistry, Registry


class MemoryRedis:
    def __init__(self):
        self.hashes = {}
        self.sets = defaultdict(set)
        self.values = {}

    async def hset(self, key, mapping):
        self.hashes.setdefault(key, {}).update(mapping)

    async def hgetall(self, key):
        return self.hashes.get(key, {})

    async def expire(self, *_):
        return True

    async def sadd(self, key, *values):
        self.sets[key].update(values)

    async def srem(self, key, *values):
        self.sets[key].difference_update(values)

    async def smembers(self, key):
        return self.sets[key].copy()

    async def sismember(self, key, value):
        return value in self.sets[key]

    async def set(self, key, value, *, nx, ex):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    async def delete(self, *keys):
        for key in keys:
            self.hashes.pop(key, None)
            self.sets.pop(key, None)
            self.values.pop(key, None)


@pytest.mark.asyncio
async def test_two_api_instances_share_tenant_scoped_connection_metadata():
    redis = MemoryRedis()
    organization_a, organization_b = uuid4(), uuid4()
    principal_a = Principal(uuid4(), uuid4(), uuid4(), organization_a, uuid4())
    principal_b = Principal(uuid4(), uuid4(), uuid4(), organization_b, uuid4())
    api_a = Registry(metadata_registry=RedisMetadataRegistry(redis, "api-a"), instance_id="api-a")
    api_b = RedisMetadataRegistry(redis, "api-b")

    connection_a = await api_a.register(principal_a)
    await api_a.register(principal_b)

    visible_to_b = await api_b.get_organization_connections(organization_a)
    assert [record["connection_id"] for record in visible_to_b] == [connection_a.id]
    assert await api_b.get_organization_connections(organization_b) != []
    assert await api_b.get_connection(connection_a.id, organization_b) is None


@pytest.mark.asyncio
async def test_multi_device_disconnect_preserves_other_shared_presence():
    redis = MemoryRedis()
    organization_id, identity_id = uuid4(), uuid4()
    registry = Registry(
        metadata_registry=RedisMetadataRegistry(redis, "api-a"), instance_id="api-a"
    )
    first = await registry.register(
        Principal(identity_id, uuid4(), uuid4(), organization_id, uuid4())
    )
    second = await registry.register(
        Principal(identity_id, uuid4(), uuid4(), organization_id, uuid4())
    )

    await registry.remove(first.id)

    records = await RedisMetadataRegistry(redis, "api-b").get_organization_connections(
        organization_id
    )
    assert [record["connection_id"] for record in records] == [second.id]


@pytest.mark.asyncio
async def test_shared_metadata_routes_subscriptions_and_deduplicates_across_instances():
    redis = MemoryRedis()
    organization_id, conversation_id = uuid4(), uuid4()
    api_a = Registry(metadata_registry=RedisMetadataRegistry(redis, "api-a"), instance_id="api-a")
    connection = await api_a.register(
        Principal(uuid4(), uuid4(), uuid4(), organization_id, uuid4())
    )
    await api_a.subscribe(connection, conversation_id)
    consumer_metadata = RedisMetadataRegistry(redis, "consumer")

    recipients = await consumer_metadata.recipients(organization_id, conversation_id)
    assert [recipient.id for recipient in recipients] == [connection.id]
    assert await consumer_metadata.claim_delivery("event-1")
    assert not await RedisMetadataRegistry(redis, "api-b").claim_delivery("event-1")


def test_api_and_consumer_factories_use_compatible_redis_metadata():
    from app.consumer_runner import build_consumer
    from app.main import build_production_registry

    redis = MemoryRedis()
    api_registry = build_production_registry(redis, "api-a")
    consumer, consumer_metadata = build_consumer(redis)

    assert isinstance(api_registry.metadata_registry, RedisMetadataRegistry)
    assert isinstance(consumer.registry, RedisMetadataRegistry)
    assert consumer.registry.redis is redis
    assert consumer_metadata.redis is redis
