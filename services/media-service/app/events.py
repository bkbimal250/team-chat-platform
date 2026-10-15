import asyncio
import json


def rabbit_callback(media_service, channel, method, _properties, body, loop=None):
    """Settle Rabbit delivery only after idempotent reference processing finishes."""
    try:
        handler = getattr(media_service, "consume_inbound_event", media_service.consume_message_event)
        work = handler(json.loads(body))
        loop.run_until_complete(work) if loop else asyncio.run(work)
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
