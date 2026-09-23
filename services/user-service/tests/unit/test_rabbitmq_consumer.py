import asyncio
import json

from app import messaging


class FakeTransaction:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, *_):
        return False


class FakeSessions:
    def begin(self):
        return FakeTransaction()


class Message:
    def __init__(self, order):
        self.body = json.dumps({"event_id": "00000000-0000-0000-0000-000000000001"}).encode()
        self.order = order

    async def ack(self):
        self.order.append("ack")

    async def nack(self, requeue=True):
        self.order.append("nack")


def test_ack_after_handler_success(monkeypatch):
    order = []

    async def success(*_):
        order.extend(["handler_start", "handler_complete"])

    monkeypatch.setattr(messaging, "sessions", FakeSessions())
    monkeypatch.setattr(messaging, "consume", success)
    asyncio.run(messaging.handle_message(Message(order)))
    assert order == ["handler_start", "handler_complete", "ack"]


def test_nack_when_handler_fails(monkeypatch):
    order = []

    async def fail(*_):
        order.append("handler_start")
        raise RuntimeError("failed")

    monkeypatch.setattr(messaging, "sessions", FakeSessions())
    monkeypatch.setattr(messaging, "consume", fail)
    asyncio.run(messaging.handle_message(Message(order)))
    assert order == ["handler_start", "nack"]
