"""Executable RabbitMQ consumer for Identity membership projections."""

import os
import signal

import pika

from app.core.config import get_settings
from app.events.consumer_transport import callback


def main() -> None:
    settings = get_settings()
    connection = pika.BlockingConnection(pika.URLParameters(str(settings.rabbitmq_url)))
    channel = connection.channel()
    channel.exchange_declare("organization.events", "topic", durable=True)
    channel.queue_declare("identity.membership", durable=True)
    channel.queue_bind("identity.membership", "organization.events", "member.#")
    channel.basic_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    channel.basic_consume("identity.membership", callback, auto_ack=False)
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: connection.add_callback_threadsafe(channel.stop_consuming))
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
