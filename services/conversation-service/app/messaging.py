"""Manual-ACK RabbitMQ adapter, intentionally opened only at runtime."""

import json

from app.db import Sessions
from app.events import consume


async def handle_message(message) -> None:
    try:
        async with Sessions.begin() as db:
            await consume(db, json.loads(message.body))
        await message.ack()
    except Exception:
        await message.nack(requeue=True)
