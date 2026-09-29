from types import SimpleNamespace

import pytest

from app import events
from app.events import consumer_callback, publish_one


class Channel:
    def __init__(self):
        self.calls = []

    def basic_ack(self, tag):
        self.calls.append(("ack", tag))

    def basic_nack(self, tag, requeue=True):
        self.calls.append(("nack", tag, requeue))


class Transaction:
    def __init__(self, event):
        self.event = event

    async def __aenter__(self):
        return SimpleNamespace(scalar=self.scalar)

    async def __aexit__(self, *_):
        return False

    async def scalar(self, _):
        return self.event


@pytest.mark.asyncio
async def test_outbox_empty_batch_returns_cleanly(monkeypatch):
    monkeypatch.setattr(events, "SessionLocal", SimpleNamespace(begin=lambda: Transaction(None)))
    assert (
        await publish_one(SimpleNamespace(publish=lambda _: pytest.fail("must not publish")))
        is False
    )


@pytest.mark.asyncio
async def test_outbox_marks_published_only_after_publish_confirmation(monkeypatch):
    event = SimpleNamespace(status="PENDING", retry_count=0, last_error="", published_at=None)
    monkeypatch.setattr(events, "SessionLocal", SimpleNamespace(begin=lambda: Transaction(event)))
    order = []

    async def confirmed(callable_, value):
        assert event.status == "PROCESSING"
        callable_(value)
        order.append("confirmed")

    monkeypatch.setattr(events.asyncio, "to_thread", confirmed)
    assert await publish_one(SimpleNamespace(publish=lambda _: order.append("publish")))
    assert order == ["publish", "confirmed"] and event.status == "PUBLISHED" and event.published_at


def test_consumer_nacks_when_processing_fails(monkeypatch):
    class Session:
        def begin(self):
            raise RuntimeError("fail")

    monkeypatch.setattr(events, "SessionLocal", Session())
    channel = Channel()
    consumer_callback(channel, SimpleNamespace(delivery_tag=1), None, b"{}")
    assert channel.calls == [("nack", 1, True)]


def test_consumer_acks_only_after_success(monkeypatch):
    class Session:
        def begin(self):
            return Transaction(None)

    async def applied(*_):
        return True

    monkeypatch.setattr(events, "SessionLocal", Session())
    monkeypatch.setattr(events, "apply_projection", applied)
    channel = Channel()
    consumer_callback(channel, SimpleNamespace(delivery_tag=2), None, b"{}")
    assert channel.calls == [("ack", 2)]
