import asyncio
import json

from app.message_notification_consumer import UnsupportedMessageEvent
from app.projection_consumers import UnsupportedProjectionEvent


async def consume_delivery(repository, event_handler, channel, delivery_tag, body):
    try:
        event = json.loads(body)
        await repository.process_event(event, lambda session: event_handler(session, event))
    except asyncio.CancelledError:
        channel.basic_nack(delivery_tag, requeue=True)
        raise
    except Exception:
        channel.basic_nack(delivery_tag, requeue=True)
    else:
        channel.basic_ack(delivery_tag)


async def consume_projection_delivery(consumer, channel, delivery_tag, body):
    """Manual-ACK adapter for projection contracts; unsupported versions are discarded."""
    try:
        event = json.loads(body)
        await consumer.consume(event)
    except UnsupportedProjectionEvent:
        channel.basic_ack(delivery_tag)
    except asyncio.CancelledError:
        channel.basic_nack(delivery_tag, requeue=True)
        raise
    except Exception:
        channel.basic_nack(delivery_tag, requeue=True)
    else:
        channel.basic_ack(delivery_tag)


async def consume_message_created_delivery(consumer, channel, delivery_tag, body):
    """Manual-ACK adapter: database commit completes before acknowledgement."""
    try:
        event = json.loads(body)
        await consumer.consume(event)
    except UnsupportedMessageEvent:
        channel.basic_ack(delivery_tag)
    except asyncio.CancelledError:
        channel.basic_nack(delivery_tag, requeue=True)
        raise
    except Exception:
        channel.basic_nack(delivery_tag, requeue=True)
    else:
        channel.basic_ack(delivery_tag)


class OutboxPublisher:
    def __init__(self, repository, publish):
        self.repository, self.publish = repository, publish

    async def publish_pending(self):
        events = await self.repository.pending_outbox()
        for event in events:
            confirmed = await self.publish(event)
            if confirmed is False:
                continue
            event.status = "PUBLISHED"
        await self.repository.session.commit()
