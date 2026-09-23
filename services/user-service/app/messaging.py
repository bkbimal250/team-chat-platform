"""RabbitMQ transport. Connections are opened only from application runtime."""

import asyncio
import json
import os
from datetime import UTC, datetime

from sqlalchemy import select

from app.events import consume
from app.main import OutboxEvent, sessions


class Broker:
    def __init__(self):
        self.connection = self.channel = None

    async def open(self):
        import aio_pika

        self.connection = await aio_pika.connect_robust(os.environ["RABBITMQ_URL"])
        self.channel = await self.connection.channel(publisher_confirms=True)
        await self.channel.set_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
        self.exchange = await self.channel.declare_exchange(
            os.getenv("RABBITMQ_EXCHANGE", "platform.events"),
            aio_pika.ExchangeType.TOPIC,
            durable=True,
        )

    async def publish(self, event: OutboxEvent):
        import aio_pika

        body = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_version": 1,
            "occurred_at": event.created_at.isoformat(),
            "producer": "user-service",
            "organization_id": str(event.organization_id) if event.organization_id else None,
            "aggregate_id": str(event.aggregate_id),
            "correlation_id": event.correlation_id,
            "payload": event.payload,
        }
        await self.exchange.publish(
            aio_pika.Message(
                body=json.dumps(body).encode(),
                correlation_id=event.correlation_id,
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key=event.event_type,
        )

    async def close(self):
        if self.connection:
            await self.connection.close()


async def handle_message(message) -> None:
    try:
        event = json.loads(message.body)
        async with sessions.begin() as db:
            await consume(db, event)
        await message.ack()
    except Exception:
        await message.nack(requeue=True)


async def publish_pending(broker: Broker, batch_size: int = 50) -> int:
    count = 0
    async with sessions.begin() as db:
        events = (
            await db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == "PENDING")
                .with_for_update(skip_locked=True)
                .limit(batch_size)
            )
        ).all()
        for event in events:
            try:
                await broker.publish(event)
                event.status, event.published_at = "PUBLISHED", datetime.now(UTC)
                count += 1
            except Exception as exc:
                event.retry_count += 1
                event.last_error = type(exc).__name__
    return count


async def outbox_loop(broker: Broker, stop: asyncio.Event) -> None:
    while not stop.is_set():
        await publish_pending(broker, int(os.getenv("OUTBOX_BATCH_SIZE", "50")))
        await asyncio.sleep(float(os.getenv("OUTBOX_POLL_SECONDS", "1")))
