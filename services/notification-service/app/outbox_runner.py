"""Executable confirmed publisher for the Notification transactional outbox."""

import asyncio
import json
import os
import signal

import pika

from app.db import SessionLocal, engine
from app.persistence import NotificationRepository
from app.rabbit import OutboxPublisher


async def run() -> None:
    connection = pika.BlockingConnection(pika.URLParameters(os.environ["RABBITMQ_URL"]))
    channel = connection.channel()
    channel.exchange_declare("notification.events", "topic", durable=True)
    channel.confirm_delivery()

    async def publish(event) -> bool:
        envelope = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_version": 1,
            "producer": "notification-service",
            "organization_id": str(event.organization_id),
            "aggregate_id": str(event.id),
            "correlation_id": str(event.event_id),
            "payload": event.payload,
        }
        return await asyncio.to_thread(
            channel.basic_publish,
            exchange="notification.events",
            routing_key=event.event_type,
            body=json.dumps(envelope).encode(),
            mandatory=True,
            properties=pika.BasicProperties(delivery_mode=2, message_id=str(event.event_id)),
        )

    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for event in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(event, stopped.set)
    try:
        while not stopped.is_set():
            async with SessionLocal() as session:
                await OutboxPublisher(NotificationRepository(session), publish).publish_pending()
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
