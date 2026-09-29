from uuid import uuid4

import pytest

from app import main
from app.auth import Principal
from app.authorization import StaticAuthorizer
from app.core import ProtocolError
from app.main import client_event, registry


@pytest.mark.asyncio
async def test_ping_subscribe_and_unsubscribe_protocol():
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    conversation = uuid4()
    main.authorizer = StaticAuthorizer(
        {(connection.principal.organization_id, connection.principal.member_id, conversation)}
    )
    assert await client_event(connection, {"version": 1, "type": "ping"}) == {
        "version": 1,
        "type": "pong",
    }
    await client_event(
        connection, {"version": 1, "type": "subscribe", "conversation_id": str(conversation)}
    )
    assert conversation in connection.subscriptions
    await client_event(
        connection, {"version": 1, "type": "unsubscribe", "conversation_id": str(conversation)}
    )
    assert conversation not in connection.subscriptions


@pytest.mark.asyncio
async def test_invalid_protocol_is_rejected():
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    with pytest.raises(ProtocolError):
        await client_event(connection, {"version": 1, "type": "unknown"})
