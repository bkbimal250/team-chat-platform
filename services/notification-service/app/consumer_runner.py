"""Production transport wiring for the existing Notification consumers."""

import asyncio
import os
import time

import pika

from app.db import engine
from app.message_notification_consumer import MessageNotificationConsumer
from app.projection_consumers import ProjectionConsumer
from app.rabbit import consume_message_created_delivery, consume_projection_delivery

EXCHANGE_ORGANIZATION = "organization.events"
EXCHANGE_MESSAGING = "messaging.events"


def _callback(adapter, consumer, loop):
    def handle(channel, method, _properties, body):
        loop.run_until_complete(adapter(consumer, channel, method.delivery_tag, body))

    return handle


def _consume() -> None:
    loop = asyncio.new_event_loop()
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE_ORGANIZATION, exchange_type="topic", durable=True)
    channel.exchange_declare(exchange=EXCHANGE_MESSAGING, exchange_type="topic", durable=True)
    channel.queue_declare(queue="notification.projections", durable=True)
    for key in ("user.#", "member.#", "conversation.#"):
        channel.queue_bind("notification.projections", EXCHANGE_ORGANIZATION, key)
    channel.queue_declare(queue="notification.message-created", durable=True)
    channel.queue_bind("notification.message-created", EXCHANGE_MESSAGING, "message.created.v1")
    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(
        "notification.projections",
        _callback(consume_projection_delivery, ProjectionConsumer(), loop),
        auto_ack=False,
    )
    channel.basic_consume(
        "notification.message-created",
        _callback(consume_message_created_delivery, MessageNotificationConsumer(), loop),
        auto_ack=False,
    )
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()
        loop.run_until_complete(engine.dispose())
        loop.close()


def main() -> None:
    while True:
        try:
            _consume()
        except pika.exceptions.AMQPError:
            time.sleep(2)


if __name__ == "__main__":
    main()
