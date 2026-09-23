import pytest

from events.outbox.models import OutboxEvent
from events.outbox.worker import publish_one
from events.publishers.rabbitmq import RabbitPublisher
from events.schemas import EventEnvelope


@pytest.mark.integration
@pytest.mark.django_db
def test_real_broker_confirm_delivery_and_manual_ack(tenants):
    with RabbitPublisher() as publisher:
        queue = publisher.channel.queue_declare(queue="", exclusive=True).method.queue
        publisher.channel.queue_bind(queue=queue, exchange="organization.events", routing_key="#")
        assert publish_one(publisher)
        method, properties, body = publisher.channel.basic_get(queue, auto_ack=False)
        assert method is not None
        envelope = EventEnvelope.model_validate_json(body)
        assert str(envelope.event_id) == properties.message_id
        assert OutboxEvent.objects.get(event_id=envelope.event_id).status == "PUBLISHED"
        publisher.channel.basic_ack(method.delivery_tag)
        assert publisher.channel.basic_get(queue, auto_ack=False)[0] is None
