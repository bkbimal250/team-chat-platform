from types import SimpleNamespace
from uuid import uuid4

import pytest

from app import main
from app.auth import Principal
from app.authorization import StaticAuthorizer
from app.events import EventConsumer, rabbit_callback
from app.main import client_event, registry
from app.registry import Registry


def test_rabbit_callback_acks_success_and_nacks_failure(monkeypatch):
    class Channel:
        def __init__(self):
            self.calls = []

        def basic_ack(self, tag):
            self.calls.append(("ack", tag))

        def basic_nack(self, tag, requeue=True):
            self.calls.append(("nack", tag, requeue))

    consumer = EventConsumer(Registry())
    channel = Channel()
    method = SimpleNamespace(delivery_tag=1)
    rabbit_callback(consumer, channel, method, None, b'{"event_id":"not-a-uuid"}')
    assert channel.calls == [("nack", 1, True)]


def test_rabbit_ack_happens_after_successful_handler(monkeypatch):
    order = []
    consumer = EventConsumer(Registry())

    async def processed(_):
        order.append("processed")
        return True

    monkeypatch.setattr(consumer, "process", processed)

    class Channel:
        def basic_ack(self, _):
            order.append("ack")

        def basic_nack(self, *_args, **_kwargs):
            pytest.fail("unexpected nack")

    rabbit_callback(consumer, Channel(), SimpleNamespace(delivery_tag=1), None, b"{}")
    assert order == ["processed", "ack"]


@pytest.mark.asyncio
async def test_typing_requires_subscription_and_stops():
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), uuid4(), uuid4()))
    conversation = uuid4()
    main.authorizer = StaticAuthorizer(
        {(connection.principal.organization_id, connection.principal.member_id, conversation)}
    )
    with pytest.raises(Exception):
        await client_event(
            connection, {"version": 1, "type": "typing.start", "conversation_id": str(conversation)}
        )
    await registry.subscribe(connection, conversation)
    await client_event(
        connection, {"version": 1, "type": "typing.start", "conversation_id": str(conversation)}
    )
    assert registry.typing
    await client_event(
        connection, {"version": 1, "type": "typing.stop", "conversation_id": str(conversation)}
    )
    assert not registry.typing
