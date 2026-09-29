from uuid import uuid4

import pytest

from app.auth import Principal
from app.registry import Registry


@pytest.mark.asyncio
async def test_registry_supports_multiple_devices_and_last_device_presence():
    registry = Registry()
    identity, org = uuid4(), uuid4()
    a = await registry.register(Principal(identity, uuid4(), uuid4(), org, uuid4()))
    b = await registry.register(Principal(identity, uuid4(), uuid4(), org, uuid4()))
    assert await registry.online_for_identity(identity)
    await registry.remove(a.id)
    assert await registry.online_for_identity(identity)
    await registry.remove(b.id)
    assert not await registry.online_for_identity(identity)


@pytest.mark.asyncio
async def test_registry_subscription_and_backpressure():
    registry = Registry(max_queue=1)
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4())
    c = await registry.register(p)
    conversation = uuid4()
    await registry.subscribe(c, conversation)
    assert await registry.recipients(p.organization_id, conversation) == [c]
    assert await registry.enqueue(c, {"x": 1}) and not await registry.enqueue(c, {"x": 2})
