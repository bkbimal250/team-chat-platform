"""Run the existing User Service transactional-outbox publisher."""

import asyncio

from app.messaging import Broker, outbox_loop


async def run() -> None:
    broker = Broker()
    await broker.open()
    try:
        await outbox_loop(broker, asyncio.Event())
    finally:
        await broker.close()


if __name__ == "__main__":
    asyncio.run(run())
