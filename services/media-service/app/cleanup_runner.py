"""Periodic orphan and unreferenced READY media cleanup."""

import asyncio
import os
import signal

from app.config import get_settings
from app.main import build_media_service


async def run_once(service) -> dict:
    return await service.run_cleanup()


async def run_loop(interval_seconds: int) -> None:
    service = build_media_service(get_settings())
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for event in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(event, stopped.set)
        except NotImplementedError:
            signal.signal(event, lambda *_: loop.call_soon_threadsafe(stopped.set))
    while not stopped.is_set():
        await run_once(service)
        try:
            await asyncio.wait_for(stopped.wait(), timeout=interval_seconds)
        except TimeoutError:
            pass


def main() -> None:
    interval = int(os.getenv("MEDIA_CLEANUP_INTERVAL_SECONDS", "3600"))
    asyncio.run(run_loop(interval))


if __name__ == "__main__":
    main()
