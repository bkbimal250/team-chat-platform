from unittest.mock import Mock

import pytest
from django.utils import timezone

from events.outbox.models import OutboxEvent
from events.outbox.worker import publish_one
from events.schemas import EventEnvelope

pytestmark = pytest.mark.django_db


def test_publish_confirmed_and_valid_schema(tenants):
    publisher = Mock()
    assert publish_one(publisher)
    event = publisher.publish.call_args.args[0]
    event.refresh_from_db()
    assert event.status == "PUBLISHED" and event.published_at
    envelope = EventEnvelope(
        event_id=event.event_id,
        event_type=event.event_type,
        occurred_at=event.created_at,
        aggregate_id=event.aggregate_id,
        organization_id=event.organization_id,
        correlation_id=event.correlation_id,
        payload=event.payload,
    )
    assert EventEnvelope.model_validate_json(envelope.model_dump_json()).event_id == event.event_id


def test_retry_preserves_id_and_exhaustion(tenants, settings):
    settings.OUTBOX_MAX_RETRIES = 2
    OutboxEvent.objects.all().update(status="PUBLISHED")
    event = OutboxEvent.objects.first()
    event.status = "PENDING"
    event.save()
    original_id = event.event_id
    publisher = Mock()
    publisher.publish.side_effect = RuntimeError("amqp://secret:secret@broker")
    assert publish_one(publisher)
    event.refresh_from_db()
    assert event.status == "PENDING" and event.retry_count == 1
    assert event.last_error == "RuntimeError"
    assert not publish_one(publisher)
    event.available_at = timezone.now()
    event.save()
    assert publish_one(publisher)
    event.refresh_from_db()
    assert event.status == "FAILED" and event.event_id == original_id


def test_publisher_requires_confirms_and_mandatory_routing(tenants):
    from unittest.mock import patch

    from events.publishers.rabbitmq import RabbitPublisher

    with patch("events.publishers.rabbitmq.pika.BlockingConnection") as connection:
        with RabbitPublisher() as publisher:
            publisher.publish(OutboxEvent.objects.first())
            publisher.channel.confirm_delivery.assert_called_once()
            kwargs = publisher.channel.basic_publish.call_args.kwargs
            assert kwargs["mandatory"] is True
            assert kwargs["properties"].delivery_mode == 2
            assert kwargs["properties"].message_id
        connection.return_value.close.assert_called_once()
