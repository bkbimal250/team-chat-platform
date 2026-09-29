import json

from app.events import consumer_transport


class Channel:
    def __init__(self):
        self.calls = []

    def basic_ack(self, tag):
        self.calls.append(("ack", tag))

    def basic_nack(self, tag, requeue=True):
        self.calls.append(("nack", tag, requeue))


class Method:
    delivery_tag = 7


def test_callback_acks_only_after_success(monkeypatch):
    order = []

    async def success(_):
        order.append("committed")
        return True

    monkeypatch.setattr(consumer_transport, "process", success)
    channel = Channel()
    consumer_transport.callback(channel, Method(), None, b"{}")
    assert order == ["committed"]
    assert channel.calls == [("ack", 7)]


def test_callback_nacks_on_failure(monkeypatch):
    async def fail(_):
        raise RuntimeError("fail")

    monkeypatch.setattr(consumer_transport, "process", fail)
    channel = Channel()
    consumer_transport.callback(channel, Method(), None, json.dumps({}).encode())
    assert channel.calls == [("nack", 7, True)]
