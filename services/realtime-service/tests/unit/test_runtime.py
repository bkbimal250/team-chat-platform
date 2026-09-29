import asyncio

import pytest

from app.runtime import Runtime


class Delivery:
    def __init__(self):
        self.acks = 0
        self.nacks = 0

    def ack(self):
        self.acks += 1

    def nack(self, requeue=True):
        self.nacks += 1
        self.requeue = requeue


class Resource:
    def __init__(self, name, calls):
        self.name, self.calls = name, calls

    async def stop(self):
        self.calls.append(f"{self.name}.stop")

    async def close(self):
        self.calls.append(f"{self.name}.close")


class AsyncCloseResource:
    def __init__(self, calls):
        self.calls = calls

    async def aclose(self):
        self.calls.append("redis.aclose")


class MetadataRegistry:
    def __init__(self, calls):
        self.calls = calls

    async def remove_instance(self):
        self.calls.append("routing.remove_instance")


@pytest.mark.asyncio
async def test_successful_delivery_acks_once():
    runtime = Runtime()
    delivery = Delivery()
    task = asyncio.create_task(asyncio.sleep(0))
    runtime.track_delivery(delivery, task)
    runtime.settle_ack(delivery)
    runtime.settle_ack(delivery)
    assert delivery.acks == 1 and delivery.nacks == 0 and not runtime.inflight_deliveries


@pytest.mark.asyncio
async def test_shutdown_nacks_unfinished_delivery_and_is_idempotent():
    runtime = Runtime()
    delivery = Delivery()
    task = asyncio.create_task(asyncio.sleep(60))
    runtime.track_delivery(delivery, task)
    await runtime.close()
    await runtime.close()
    assert delivery.acks == 0 and delivery.nacks == 1 and runtime.state == "STOPPED"


@pytest.mark.asyncio
async def test_shutdown_stops_consumer_cleans_routing_and_closes_resources():
    calls = []
    delivery = Delivery()
    task = asyncio.create_task(asyncio.sleep(60))
    runtime = Runtime(
        rabbit_consumer=Resource("consumer", calls),
        rabbit_channel=Resource("channel", calls),
        rabbit_connection=Resource("connection", calls),
        redis_client=AsyncCloseResource(calls),
        metadata_registry=MetadataRegistry(calls),
    )
    runtime.track_delivery(delivery, task)

    await runtime.shutdown()

    assert delivery.nacks == 1
    assert calls == [
        "consumer.stop",
        "routing.remove_instance",
        "consumer.close",
        "channel.close",
        "connection.close",
        "redis.aclose",
    ]
    assert runtime.state == "STOPPED"
