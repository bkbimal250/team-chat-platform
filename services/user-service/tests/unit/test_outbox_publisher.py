import asyncio

from app import messaging


class Event:
    def __init__(self):
        self.status = "PENDING"
        self.retry_count = 0
        self.last_error = ""
        self.published_at = None


class Result:
    def __init__(self, rows):
        self.rows = rows

    def scalars(self):
        return self

    def all(self):
        return self.rows


class Session:
    def __init__(self, rows):
        self.rows = rows

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def scalars(self, _):
        return Result(self.rows)


class Sessions:
    def __init__(self, rows):
        self.rows = rows

    def begin(self):
        return Session(self.rows)


def test_empty_batch_does_nothing(monkeypatch):
    monkeypatch.setattr(messaging, "sessions", Sessions([]))
    assert asyncio.run(messaging.publish_pending(object())) == 0


def test_publish_success_marks_event_after_publish(monkeypatch):
    event, order = Event(), []

    class Broker:
        async def publish(self, value):
            order.append("publish")
            assert value.status == "PENDING"

    monkeypatch.setattr(messaging, "sessions", Sessions([event]))
    assert asyncio.run(messaging.publish_pending(Broker())) == 1
    assert order == ["publish"] and event.status == "PUBLISHED" and event.published_at is not None


def test_publish_failure_keeps_event_retryable(monkeypatch):
    event = Event()

    class Broker:
        async def publish(self, _):
            raise RuntimeError("broker unavailable")

    monkeypatch.setattr(messaging, "sessions", Sessions([event]))
    assert asyncio.run(messaging.publish_pending(Broker())) == 0
    assert (
        event.status == "PENDING" and event.retry_count == 1 and event.last_error == "RuntimeError"
    )
