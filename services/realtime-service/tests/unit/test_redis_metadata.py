import asyncio
from uuid import uuid4

import pytest

from app.auth import Principal
from app.registry import Connection, RedisMetadataRegistry


class Redis:
    def __init__(self):
        self.calls = []
        self.claims = set()

    async def hset(self, *args, **kwargs):
        self.calls.append(("hset", args, kwargs))

    async def expire(self, *args):
        self.calls.append(("expire", args))

    async def delete(self, *args):
        self.calls.append(("delete", args))

    async def sadd(self, *args):
        self.calls.append(("sadd", args))

    async def smembers(self, *_):
        return {"c"}

    async def set(self, key, value, *, nx, ex):
        self.calls.append(("set", (key, value), {"nx": nx, "ex": ex}))
        if key in self.claims:
            return False
        self.claims.add(key)
        return True


@pytest.mark.asyncio
async def test_redis_metadata_registration_and_removal():
    redis = Redis()
    connection = Connection(
        "c", Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()), asyncio.Queue()
    )
    registry = RedisMetadataRegistry(redis, "instance-a")
    assert await registry.register(connection) == "realtime:connection:c"
    await registry.remove("c")
    assert [call[0] for call in redis.calls] == [
        "hset",
        "expire",
        "sadd",
        "expire",
        "sadd",
        "expire",
        "delete",
    ]


@pytest.mark.asyncio
async def test_claim_delivery_uses_shared_redis_nx_ex_semantics():
    redis = Redis()
    registry_a = RedisMetadataRegistry(redis, "instance-a")
    registry_b = RedisMetadataRegistry(redis, "instance-b")

    assert await registry_a.claim_delivery("delivery-123", ttl=42)
    assert not await registry_b.claim_delivery("delivery-123", ttl=42)
    assert redis.calls[-2:] == [
        ("set", ("realtime:delivery:delivery-123", "1"), {"nx": True, "ex": 42}),
        ("set", ("realtime:delivery:delivery-123", "1"), {"nx": True, "ex": 42}),
    ]
