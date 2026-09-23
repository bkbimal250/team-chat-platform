import pika
from django.conf import settings

from events.schemas import EventEnvelope


class RabbitPublisher:
    """At-least-once publisher. Persistent messages, mandatory routing and confirms."""

    def __enter__(self):
        parameters = pika.URLParameters(settings.RABBITMQ_URL)
        parameters.socket_timeout = 5
        parameters.stack_timeout = 10
        parameters.blocked_connection_timeout = 10
        parameters.heartbeat = 30
        self.connection = pika.BlockingConnection(parameters)
        self.channel = self.connection.channel()
        self.declare_topology()
        self.channel.confirm_delivery()
        return self

    def declare_topology(self):
        self.channel.exchange_declare(
            exchange=settings.RABBITMQ_EXCHANGE, exchange_type="topic", durable=True
        )
        self.channel.exchange_declare(
            exchange="organization.dead", exchange_type="topic", durable=True
        )
        self.channel.queue_declare(
            queue="organization.events.archive",
            durable=True,
            arguments={"x-dead-letter-exchange": "organization.dead"},
        )
        self.channel.queue_bind(
            queue="organization.events.archive",
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key="#",
        )
        self.channel.queue_declare(queue="organization.events.dead", durable=True)
        self.channel.queue_bind(
            queue="organization.events.dead", exchange="organization.dead", routing_key="#"
        )

    def publish(self, event):
        envelope = EventEnvelope(
            event_id=event.event_id,
            event_type=event.event_type,
            occurred_at=event.created_at,
            organization_id=event.organization_id,
            aggregate_id=event.aggregate_id,
            correlation_id=event.correlation_id,
            payload=event.payload,
        )
        self.channel.basic_publish(
            exchange=settings.RABBITMQ_EXCHANGE,
            routing_key=event.event_type,
            body=envelope.model_dump_json().encode(),
            mandatory=True,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=str(event.event_id),
                correlation_id=event.correlation_id,
            ),
        )

    def __exit__(self, *args):
        if self.connection.is_open:
            self.connection.close()
