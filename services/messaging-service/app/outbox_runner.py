"""Run the existing Messaging transactional-outbox publisher."""

import asyncio

from app.events import Publisher, publish_one


async def run() -> None:
    while True:
        try:
            with Publisher() as publisher:
                while await publish_one(publisher):
                    pass
        except Exception:
            pass
        await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(run())
