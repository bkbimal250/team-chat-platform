"""Executable RabbitMQ consumer for durable Media references."""

import os
import signal

import pika

from app.config import get_settings
from app.events import rabbit_callback
from app.main import build_media_service


def main() -> None:
    service = build_media_service(get_settings())
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.exchange_declare("messaging.events", "topic", durable=True)
    channel.queue_declare("media.references", durable=True)
    for key in ("message.created.v1", "message.deleted.v1"):
        channel.queue_bind("media.references", "messaging.events", key)
    channel.basic_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    channel.basic_consume(
        "media.references",
        lambda ch, method, properties, body: rabbit_callback(service, ch, method, properties, body),
        auto_ack=False,
    )
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: connection.add_callback_threadsafe(channel.stop_consuming))
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
