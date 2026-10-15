from collections import defaultdict
from uuid import uuid4

import pytest

from app.auth import Principal
from app.presence import PresenceService


class MemoryRedis:
    def __init__(self):
        self.hashes = defaultdict(dict)
        self.ttl = {}

    async def exists(self, key):
        return key in self.hashes and bool(self.hashes[key])

    async def hset(self, key, field, value):
        self.hashes[key][field] = value

    async def hdel(self, key, field):
        self.hashes[key].pop(field, None)

    async def hlen(self, key):
        return len(self.hashes.get(key, {}))

    async def expire(self, key, _ttl):
        self.ttl[key] = _ttl

    async def delete(self, key):
        self.hashes.pop(key, None)
        self.ttl.pop(key, None)


@pytest.mark.asyncio
async def test_presence_stays_online_until_last_device_disconnects():
    redis = MemoryRedis()
    presence = PresenceService(redis)
    identity = uuid4()
    first = Principal(identity, uuid4(), uuid4(), uuid4(), uuid4())
    second = Principal(identity, uuid4(), uuid4(), uuid4(), uuid4())

    await presence.touch(first)
    await presence.touch(second)
    assert (await presence.snapshot(identity))["online"]

    await presence.clear(first)
    assert (await presence.snapshot(identity))["online"]

    await presence.clear(second)
    assert not (await presence.snapshot(identity))["online"]
