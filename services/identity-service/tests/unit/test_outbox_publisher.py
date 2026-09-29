from types import SimpleNamespace

import pytest

from app.events import worker
from app.models.models import OutboxStatus


class Result:
    def __init__(self, event):
        self.event = event

    def scalar_one_or_none(self):
        return self.event


class Db:
    async def execute(self, _):
        return Result(self.event)


class Transaction:
    def __init__(self, event):
        self.event = event

    async def __aenter__(self):
        return DbWithEvent(self.event)

    async def __aexit__(self, *args):
        return False


class DbWithEvent(Db):
    def __init__(self, event):
        self.event = event


class Sessions:
    def __init__(self, event):
        self.event = event

    def begin(self):
        return Transaction(self.event)


@pytest.mark.asyncio
async def test_outbox_publish_failure_is_retried(monkeypatch):
    event = SimpleNamespace(
        status=OutboxStatus.PENDING, retry_count=0, last_error="", available_at=None
    )
    monkeypatch.setattr(worker, "SessionLocal", Sessions(event))

    async def fail(*args, **kwargs):
        raise ConnectionError()

    monkeypatch.setattr(worker.asyncio, "to_thread", fail)

    assert await worker.publish_one(SimpleNamespace(publish=lambda _: None)) is True
    assert event.status == OutboxStatus.PENDING
    assert event.retry_count == 1
    assert event.last_error == "ConnectionError"


@pytest.mark.asyncio
async def test_empty_outbox_batch_does_nothing(monkeypatch):
    monkeypatch.setattr(worker, "SessionLocal", Sessions(None))
    publisher = SimpleNamespace(publish=lambda _: pytest.fail("publish must not be called"))

    assert await worker.publish_one(publisher) is False


@pytest.mark.asyncio
async def test_successful_outbox_publication_marks_event_published(monkeypatch):
    order = []

    class Event:
        def __init__(self):
            self._status = OutboxStatus.PENDING
            self.retry_count = 0
            self.last_error = ""
            self.available_at = None
            self.published_at = None
            self.event_type = "session.created.v1"
            self.payload = {"resource_id": "session-1"}
            self.correlation_id = "correlation-1"

        @property
        def status(self):
            return self._status

        @status.setter
        def status(self, value):
            self._status = value
            if value == OutboxStatus.PUBLISHED:
                order.append("published")

    event = Event()
    monkeypatch.setattr(worker, "SessionLocal", Sessions(event))

    class Publisher:
        def publish(self, received):
            assert received is event
            assert received.event_type == "session.created.v1"
            assert received.payload == {"resource_id": "session-1"}
            assert received.correlation_id == "correlation-1"
            order.append("publish")

    async def confirmed(callable_, received):
        assert event.status == OutboxStatus.PROCESSING
        callable_(received)
        order.append("confirmed")

    monkeypatch.setattr(worker.asyncio, "to_thread", confirmed)

    assert await worker.publish_one(Publisher()) is True
    assert order == ["publish", "confirmed", "published"]
    assert event.status == OutboxStatus.PUBLISHED
    assert event.published_at is not None
    assert event.last_error == ""
