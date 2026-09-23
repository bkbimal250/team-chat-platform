import json

import pika

from app.core.config import get_settings


class RabbitPublisher:
    def __enter__(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(get_settings().rabbitmq_url))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange="organization.events", exchange_type="topic", durable=True
        )
        self.channel.confirm_delivery()
        return self

    def publish(self, event) -> None:
        envelope = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_version": event.event_version,
            "occurred_at": event.created_at.isoformat(),
            "producer": "identity-service",
            "organization_id": str(event.organization_id) if event.organization_id else None,
            "aggregate_id": str(event.aggregate_id),
            "correlation_id": event.correlation_id,
            "payload": event.payload,
        }
        self.channel.basic_publish(
            exchange="organization.events",
            routing_key=event.event_type,
            body=json.dumps(envelope).encode(),
            mandatory=True,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=str(event.event_id),
                correlation_id=event.correlation_id,
            ),
        )

    def __exit__(self, *args):
        self.connection.close()
