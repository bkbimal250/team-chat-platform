import asyncio
import uuid

from app import events


class FakeDb:
    def __init__(self):
        self.added = []
        self.calls = 0

    async def scalar(self, *_):
        self.calls += 1
        return "duplicate" if self.calls == 1 and getattr(self, "duplicate", False) else None

    def add(self, value):
        self.added.append(value)

    def add_all(self, values):
        self.added.extend(values)

    async def flush(self):
        pass


def identity_event():
    return {
        "event_id": str(uuid.uuid4()),
        "event_type": "identity.created.v1",
        "producer": "identity-service",
        "correlation_id": "c",
        "payload": {"identity_id": str(uuid.uuid4()), "display_name": "Ada"},
    }


def test_identity_created_creates_user_preferences_privacy_and_outbox():
    db = FakeDb()
    assert asyncio.run(events.consume(db, identity_event())) is True
    names = {type(value).__name__ for value in db.added}
    assert {
        "User",
        "UserPreferences",
        "UserPrivacySettings",
        "ProcessedEvent",
        "OutboxEvent",
    } <= names


def test_duplicate_identity_event_is_idempotent():
    db = FakeDb()
    db.duplicate = True
    assert asyncio.run(events.consume(db, identity_event())) is False
    assert db.added == []
