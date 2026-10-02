"""Executable confirmed publisher for the Media transactional outbox."""

import asyncio
import json
import os
import signal

import pika
from sqlalchemy import select

from app.db import SessionLocal, engine
from app.models import OutboxEvent


async def publish_batch(channel, limit: int = 100) -> int:
    async with SessionLocal.begin() as session:
        events = list(
            await session.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == "PENDING")
                .with_for_update(skip_locked=True)
                .limit(limit)
            )
        )
        for event in events:
            envelope = {
                "event_id": str(event.id),
                "event_type": event.event_type,
                "event_version": event.event_version,
                "producer": "media-service",
                "organization_id": str(event.organization_id),
                "aggregate_id": str(event.aggregate_id),
                "correlation_id": event.correlation_id,
                "payload": json.loads(event.payload),
            }
            confirmed = await asyncio.to_thread(
                channel.basic_publish,
                exchange="media.events",
                routing_key=event.event_type,
                body=json.dumps(envelope).encode(),
                mandatory=True,
                properties=pika.BasicProperties(delivery_mode=2, message_id=str(event.id)),
            )
            if confirmed is False:
                raise RuntimeError("RabbitMQ publisher confirmation failed")
            event.status = "PUBLISHED"
        return len(events)


async def run() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.exchange_declare("media.events", "topic", durable=True)
    channel.confirm_delivery()
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for event in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(event, stopped.set)
    try:
        while not stopped.is_set():
            if not await publish_batch(channel):
                try:
                    await asyncio.wait_for(stopped.wait(), timeout=1)
                except TimeoutError:
                    pass
    finally:
        if connection.is_open:
            connection.close()
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(run())
