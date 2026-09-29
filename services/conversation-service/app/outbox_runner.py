"""Run the existing Conversation transactional-outbox publisher."""

import asyncio

from app.outbox import publish_pending
from app.publisher import RabbitPublisher


async def run() -> None:
    while True:
        try:
            with RabbitPublisher() as publisher:
                while await publish_pending(publisher):
                    pass
        except Exception:
            pass
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())
