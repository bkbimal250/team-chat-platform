"""Executable RabbitMQ consumer for User identity projections."""

import asyncio
import os
import signal

import aio_pika

from app.messaging import handle_message


async def run() -> None:
    connection = await aio_pika.connect_robust(os.environ["RABBITMQ_URL"])
    channel = await connection.channel()
    await channel.set_qos(prefetch_count=int(os.getenv("RABBITMQ_PREFETCH_COUNT", "20")))
    exchange = await channel.declare_exchange(
        "organization.events", aio_pika.ExchangeType.TOPIC, durable=True
    )
    queue = await channel.declare_queue("user.identity", durable=True)
    await queue.bind(exchange, "identity.#")
    await queue.consume(handle_message, no_ack=False)
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for event in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(event, stopped.set)
    try:
        await stopped.wait()
    finally:
        await connection.close()


if __name__ == "__main__":
    asyncio.run(run())
