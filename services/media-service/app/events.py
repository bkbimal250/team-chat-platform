import asyncio
import json


def rabbit_callback(media_service, channel, method, _properties, body, loop=None):
    """Settle Rabbit delivery only after idempotent reference processing finishes."""
    try:
        loop.run_until_complete(
            media_service.consume_message_event(json.loads(body))
        ) if loop else asyncio.run(media_service.consume_message_event(json.loads(body)))
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
