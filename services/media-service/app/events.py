import asyncio
import json


def rabbit_callback(media_service, channel, method, _properties, body):
    """Settle Rabbit delivery only after idempotent reference processing finishes."""
    try:
        asyncio.run(media_service.consume_message_event(json.loads(body)))
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
