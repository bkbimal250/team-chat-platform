from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

from app.events import Publisher


def test_publisher_serializes_common_message_envelope(monkeypatch):
    captured = {}
    publisher = Publisher.__new__(Publisher)
    publisher.channel = SimpleNamespace(basic_publish=lambda **kwargs: captured.update(kwargs))
    event = SimpleNamespace(
        event_id=uuid4(),
        event_type="message.created.v1",
        created_at=datetime.now(UTC),
        organization_id=uuid4(),
        aggregate_id=uuid4(),
        correlation_id="c",
        payload={"message_id": "x"},
    )
    publisher.publish(event)
    assert captured["routing_key"] == "message.created.v1"
    assert b'"event_type": "message.created.v1"' in captured["body"]
