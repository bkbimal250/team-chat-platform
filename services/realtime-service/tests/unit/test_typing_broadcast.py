import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.auth import Principal
from app.registry import Registry
from app.typing import TypingBroadcaster


@pytest.mark.asyncio
@pytest.mark.parametrize("personal", [False, True])
async def test_typing_is_tenant_scoped_authorized_and_excludes_sender(personal):
    registry = Registry()
    org, cid = (None if personal else uuid4()), uuid4()
    sender = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    peer = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    foreign = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    denied = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    elsewhere = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    for connection in (sender, peer, foreign, denied):
        await registry.subscribe(connection, cid)

    async def authorize(principal, conversation):
        if principal.member_id == denied.principal.member_id:
            raise ValueError("Not a participant")
        assert conversation == cid

    broadcast = TypingBroadcaster(registry, authorize, ttl=0.01)
    await broadcast.update(sender, cid, True)
    assert (await peer.queue.get())["payload"]["active"] is True
    assert (
        sender.queue.empty()
        and foreign.queue.empty()
        and denied.queue.empty()
        and elsewhere.queue.empty()
    )
    await asyncio.sleep(0.03)
    assert (await peer.queue.get())["payload"]["active"] is False
    assert not registry.typing and not broadcast.tasks
    await broadcast.close()


@pytest.mark.asyncio
async def test_typing_disconnect_clears_ephemeral_state():
    registry = Registry()
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    cid = uuid4()
    broadcaster = TypingBroadcaster(registry, AsyncMock())
    await broadcaster.update(connection, cid, True)
    await broadcaster.remove(connection)
    assert not registry.typing and not broadcaster.tasks
    await broadcaster.close()


@pytest.mark.asyncio
async def test_typing_remote_fanout_uses_existing_instance_channel():
    import json
    from types import SimpleNamespace

    registry = Registry(instance_id="source")
    org, cid = uuid4(), uuid4()
    sender = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, uuid4()))
    target = SimpleNamespace(
        id="remote-connection",
        instance_id="remote",
        principal=Principal(uuid4(), uuid4(), uuid4(), org, uuid4()),
    )
    metadata = SimpleNamespace(
        recipients=AsyncMock(return_value=[target]), redis=SimpleNamespace(publish=AsyncMock())
    )
    registry.metadata_registry = metadata
    authorize = AsyncMock()
    broadcaster = TypingBroadcaster(registry, authorize)
    await broadcaster.broadcast(sender, cid, True)
    channel, body = metadata.redis.publish.call_args.args
    assert channel == "realtime:instance:remote:deliveries"
    payload = json.loads(body)
    assert payload["organization_id"] == str(org) and payload["connection_id"] == target.id
    assert payload["event"]["payload"]["conversation_id"] == str(cid)
    authorize.assert_awaited_once_with(target.principal, cid)
    await broadcaster.close()
