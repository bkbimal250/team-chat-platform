"""Executable RabbitMQ consumer for Messaging authorization projections."""

import os
import signal

import pika

from app.core import settings
from app.events import consumer_callback


def main() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(settings().rabbitmq_url))
    channel = connection.channel()
    channel.exchange_declare("organization.events", "topic", durable=True)
    channel.queue_declare("messaging.authorization", durable=True)
    for key in ("conversation.#", "member.#", "block.#"):
        channel.queue_bind("messaging.authorization", "organization.events", key)
    channel.basic_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    channel.basic_consume("messaging.authorization", consumer_callback, auto_ack=False)
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: connection.add_callback_threadsafe(channel.stop_consuming))
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
