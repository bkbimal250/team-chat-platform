from dataclasses import dataclass, field


@dataclass
class Runtime:
    state: str = "RUNNING"
    redis_client: object | None = None
    rabbit_connection: object | None = None
    rabbit_channel: object | None = None
    rabbit_consumer: object | None = None
    metadata_registry: object | None = None
    inflight_tasks: set = field(default_factory=set)
    inflight_deliveries: dict = field(default_factory=dict)
    _shutdown_task: object | None = None

    def track_delivery(self, delivery, task):
        self.inflight_deliveries[id(delivery)] = {
            "delivery": delivery,
            "task": task,
            "acked": False,
            "nacked": False,
        }

    def settle_ack(self, delivery):
        item = self.inflight_deliveries.get(id(delivery))
        if item and not item["acked"] and not item["nacked"]:
            delivery.ack()
            item["acked"] = True
        self.inflight_deliveries.pop(id(delivery), None)

    def settle_nack(self, delivery):
        item = self.inflight_deliveries.get(id(delivery))
        if item and not item["acked"] and not item["nacked"]:
            delivery.nack(requeue=True)
            item["nacked"] = True
        self.inflight_deliveries.pop(id(delivery), None)

    async def close(self):
        if self.state == "STOPPED":
            return
        if self.state == "DRAINING":
            return
        self.state = "DRAINING"
        stop = getattr(self.rabbit_consumer, "stop", None)
        if stop:
            await stop()
        for item in list(self.inflight_deliveries.values()):
            item["task"].cancel()
            self.settle_nack(item["delivery"])
        for task in list(self.inflight_tasks):
            task.cancel()
        remove_instance = getattr(self.metadata_registry, "remove_instance", None)
        if remove_instance:
            result = remove_instance()
            if hasattr(result, "__await__"):
                await result
        for resource in (
            self.rabbit_consumer,
            self.rabbit_channel,
            self.rabbit_connection,
            self.redis_client,
        ):
            close = getattr(resource, "close", None)
            if not close:
                close = getattr(resource, "aclose", None)
            if close:
                result = close()
                if hasattr(result, "__await__"):
                    await result
        self.state = "STOPPED"

    async def shutdown(self):
        await self.close()
