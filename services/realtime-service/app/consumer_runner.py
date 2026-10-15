"""Production transport wiring for the Realtime event consumer."""

import asyncio
import json
import os
import time

import pika
import redis
from redis.asyncio import Redis

from app.core import settings
from app.events import EventConsumer, rabbit_callback
from app.org_membership import RedisOrgMembershipStore
from app.registry import RedisMetadataRegistry

EXCHANGE_ORGANIZATION = "organization.events"
EXCHANGE_MESSAGING = "messaging.events"


def build_consumer(redis_client):
    configured = settings()
    store = RedisOrgMembershipStore(redis_client)
    metadata = RedisMetadataRegistry(redis_client, configured.instance_id, store)

    async def remote_publish(event: dict) -> None:
        payload = event["payload"]
        channel = f"realtime:instance:{payload['target_instance_id']}:deliveries"
        await redis_client.publish(
            channel,
            json.dumps({**payload, "organization_id": event["organization_id"]}),
        )

    async def on_workspace_revoke(payload: dict) -> None:
        await redis_client.publish("realtime:workspace-revocations", json.dumps(payload))

    return EventConsumer(
        metadata,
        f"consumer:{configured.instance_id}",
        remote_publish,
        metadata.claim_delivery,
        on_workspace_revoke,
    ), metadata


def _validate_consumer_env() -> None:
    if os.environ.get("APP_ENV", "development") != "production":
        return
    rabbit = os.environ.get("RABBITMQ_URL", "")
    if not rabbit:
        raise RuntimeError("Production consumer requires RABBITMQ_URL")
    from urllib.parse import urlparse

    host = urlparse(rabbit).hostname
    if host in {None, "localhost", "127.0.0.1"}:
        raise RuntimeError("Production consumer requires external RABBITMQ_URL")


def _consume() -> None:
    _validate_consumer_env()
    redis_url = os.environ["REDIS_URL"]
    redis_client = Redis.from_url(redis_url)
    loop = asyncio.new_event_loop()
    metadata = None
    connection = None
    try:
        loop.run_until_complete(redis_client.ping())
        consumer, metadata = build_consumer(redis_client)
        connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
        channel = connection.channel()
        for exchange in (EXCHANGE_ORGANIZATION, EXCHANGE_MESSAGING):
            channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        channel.queue_declare(queue="realtime.events", durable=True)
        for exchange, key in (
            (EXCHANGE_ORGANIZATION, "conversation.#"),
            (EXCHANGE_ORGANIZATION, "member.#"),
            (EXCHANGE_MESSAGING, "message.#"),
        ):
            channel.queue_bind("realtime.events", exchange, key)
        channel.basic_qos(prefetch_count=1)
        channel.basic_consume(
            "realtime.events",
            lambda ch, method, properties, body: rabbit_callback(
                consumer, ch, method, properties, body, loop
            ),
            auto_ack=False,
        )
        channel.start_consuming()
    finally:
        if metadata:
            loop.run_until_complete(metadata.remove_instance())
        loop.run_until_complete(redis_client.aclose())
        if connection and connection.is_open:
            connection.close()
        loop.close()


def main() -> None:
    while True:
        try:
            _consume()
        except (pika.exceptions.AMQPError, redis.RedisError):
            time.sleep(2)


if __name__ == "__main__":
    main()
