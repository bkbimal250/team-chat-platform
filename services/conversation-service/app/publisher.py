"""Confirmed RabbitMQ publisher for the Conversation transactional outbox."""

import json

import pika

from app.core import settings


class RabbitPublisher:
    def __enter__(self):
        parameters = pika.URLParameters(settings().rabbitmq_url)
        parameters.socket_timeout = 5
        parameters.stack_timeout = 10
        parameters.blocked_connection_timeout = 10
        parameters.heartbeat = 30
        self.connection = pika.BlockingConnection(parameters)
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
            "event_version": 1,
            "occurred_at": event.created_at.isoformat(),
            "producer": "conversation-service",
            "organization_id": str(event.organization_id),
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

    def __exit__(self, *_):
        if self.connection.is_open:
            self.connection.close()
