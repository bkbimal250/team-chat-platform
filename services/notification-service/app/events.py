import asyncio
import json


def rabbit_callback(service, channel, method, _properties, body):
    try:
        asyncio.run(service.consume(json.loads(body)))
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)
