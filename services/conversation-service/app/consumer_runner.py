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


def callback(channel, method, _properties, body, loop=None):
    work = handle_message(Delivery(channel, method.delivery_tag, body))
    loop.run_until_complete(work) if loop else asyncio.run(work)


def main() -> None:
    loop = asyncio.new_event_loop()
    connection = pika.BlockingConnection(pika.URLParameters(str(settings().rabbitmq_url)))
    channel = connection.channel()
    channel.exchange_declare("organization.events", "topic", durable=True)
    channel.queue_declare("conversation.membership", durable=True)
    for key in ("member.#", "organization.#"):
        channel.queue_bind("conversation.membership", "organization.events", key)
    for exchange, keys in (
        (
            "messaging.events",
            (
                "message.created.v1",
                "message.edited.v1",
                "message.deleted.v1",
                "message.read.v1",
                "conversation.summary.message.v1",
                "conversation.summary.read.v1",
            ),
        ),
        ("user.events", ("user.blocked.v1", "user.unblocked.v1")),
    ):
        channel.exchange_declare(exchange, "topic", durable=True)
        for key in keys:
            channel.queue_bind("conversation.membership", exchange, key)
    channel.basic_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    channel.basic_consume(
        "conversation.membership",
        lambda ch, method, props, body: callback(ch, method, props, body, loop),
        auto_ack=False,
    )
    for event in (signal.SIGTERM, signal.SIGINT):
        signal.signal(event, lambda *_: connection.add_callback_threadsafe(channel.stop_consuming))
    try:
        channel.start_consuming()
    finally:
        if connection.is_open:
            connection.close()
        loop.close()


if __name__ == "__main__":
    main()
