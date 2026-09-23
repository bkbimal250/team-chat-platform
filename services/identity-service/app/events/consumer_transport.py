"""RabbitMQ callback boundary: ACK only after the projection transaction commits."""

import asyncio
import json

from app.db.session import SessionLocal
from app.events.consumers import apply_membership_event


async def process(body: bytes) -> bool:
    envelope = json.loads(body)
    async with SessionLocal.begin() as db:
        return await apply_membership_event(db, envelope)


def callback(channel, method, _properties, body: bytes) -> None:
    try:
        asyncio.run(process(body))
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
