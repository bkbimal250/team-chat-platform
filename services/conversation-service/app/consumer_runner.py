"""Executable RabbitMQ consumer for Conversation projections."""

import asyncio
import os
import signal

import pika

from app.core import settings
from app.messaging import handle_message


class Delivery:
    def __init__(self, channel, delivery_tag, body):
        self.channel, self.delivery_tag, self.body = channel, delivery_tag, body

    async def ack(self):
        self.channel.basic_ack(self.delivery_tag)

    async def nack(self, requeue=True):
        self.channel.basic_nack(self.delivery_tag, requeue=requeue)


def callback(channel, method, _properties, body):
    asyncio.run(handle_message(Delivery(channel, method.delivery_tag, body)))


def main() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(str(settings().rabbitmq_url)))
    channel = connection.channel()
    channel.exchange_declare("organization.events", "topic", durable=True)
    channel.queue_declare("conversation.membership", durable=True)
    for key in ("member.#", "organization.#"):
        channel.queue_bind("conversation.membership", "organization.events", key)
    channel.basic_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    channel.basic_consume("conversation.membership", callback, auto_ack=False)
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: connection.add_callback_threadsafe(channel.stop_consuming))
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()


if __name__ == "__main__":
    main()
