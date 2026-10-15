import asyncio
from uuid import uuid4

import pytest

from app.auth import Principal
from app.registry import Registry


@pytest.mark.asyncio
async def test_queue_overflow_signals_resync_required():
    registry = Registry(max_queue=1)
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    await registry.enqueue(connection, {"version": 1, "type": "message.created.v1", "payload": {}})
    assert await registry.enqueue(
        connection, {"version": 1, "type": "message.created.v1", "payload": {}}
    ) is False
    assert connection.resync_required
    frame = await asyncio.wait_for(connection.queue.get(), timeout=1)
    assert frame["type"] == "connection.resync_required.v1"
