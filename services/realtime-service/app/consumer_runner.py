"""Production transport wiring for the existing Realtime event consumer."""

import asyncio
import json
import os
import time

import pika
import redis

from app.core import settings
from app.events import EventConsumer, rabbit_callback
from app.registry import RedisMetadataRegistry

EXCHANGE_ORGANIZATION = "organization.events"
EXCHANGE_MESSAGING = "messaging.events"
EXCHANGE_REALTIME = "realtime.events"


def build_consumer(redis_client):
    """Use the same serializable Redis routing metadata as the API process."""
    configured = settings()
    metadata = RedisMetadataRegistry(redis_client, configured.instance_id)

    async def remote_publish(event: dict) -> None:
        payload = event["payload"]
        channel = f"realtime:instance:{payload['target_instance_id']}:deliveries"
        await asyncio.to_thread(
            redis_client.publish,
            channel,
            json.dumps({**payload, "organization_id": event["organization_id"]}),
        )

    return EventConsumer(
        metadata, f"consumer:{configured.instance_id}", remote_publish, metadata.claim_delivery
    ), metadata


def _consume() -> None:
    redis_url = os.environ["REDIS_URL"]
    redis_client = redis.Redis.from_url(redis_url)
    metadata = None
    connection = None
    try:
        # Fail before RabbitMQ consumption if shared production metadata is unavailable.
        redis_client.ping()
        consumer, metadata = build_consumer(redis_client)
        connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
        channel = connection.channel()
        for exchange in (EXCHANGE_ORGANIZATION, EXCHANGE_MESSAGING, EXCHANGE_REALTIME):
            channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        channel.queue_declare(queue="realtime.events", durable=True)
        for exchange, key in (
            (EXCHANGE_ORGANIZATION, "conversation.#"),
            (EXCHANGE_MESSAGING, "message.#"),
        ):
            channel.queue_bind("realtime.events", exchange, key)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            "realtime.events",
            lambda ch, method, properties, body: rabbit_callback(
                consumer, ch, method, properties, body
            ),
            auto_ack=False,
        )
        channel.start_consuming()
    finally:
        if metadata:
            asyncio.run(metadata.remove_instance())
        redis_client.close()
        if connection and connection.is_open:
            connection.close()


def main() -> None:
    while True:
        try:
            _consume()
        except (pika.exceptions.AMQPError, redis.RedisError):
            time.sleep(2)


if __name__ == "__main__":
    main()
