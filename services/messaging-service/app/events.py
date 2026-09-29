import asyncio
import json
from datetime import UTC, datetime
from uuid import UUID

import pika
from sqlalchemy import select

from app.core import settings
from app.db import SessionLocal
from app.models import (
    BlockProjection,
    ConversationMemberProjection,
    ConversationProjection,
    OutboxEvent,
    ProcessedEvent,
)


async def apply_projection(db, envelope: dict) -> bool:
    event_id = UUID(envelope["event_id"])
    if await db.scalar(select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)):
        return False
    payload, event_type = envelope["payload"], envelope["event_type"]
    organization_id = UUID(str(envelope["organization_id"]))
    if event_type == "user.blocked.v1":
        db.add(
            BlockProjection(
                blocker_user_id=UUID(str(payload["blocker_user_id"])),
                blocked_user_id=UUID(str(payload["blocked_user_id"])),
            )
        )
    elif event_type == "user.unblocked.v1":
        row = await db.scalar(
            select(BlockProjection).where(
                BlockProjection.blocker_user_id == UUID(str(payload["blocker_user_id"])),
                BlockProjection.blocked_user_id == UUID(str(payload["blocked_user_id"])),
            )
        )
        if row:
            await db.delete(row)
    else:
        conversation_id = UUID(str(payload.get("conversation_id") or envelope["aggregate_id"]))
        if event_type == "conversation.created.v1":
            db.add(
                ConversationProjection(
                    id=conversation_id,
                    organization_id=organization_id,
                    type=payload["type"],
                    status="ACTIVE",
                )
            )
            for member in payload.get("members", []):
                db.add(
                    ConversationMemberProjection(
                        conversation_id=conversation_id,
                        organization_id=organization_id,
                        member_id=UUID(str(member["member_id"])),
                        user_id=UUID(str(member["user_id"])),
                        status=member.get("status", "ACTIVE"),
                    )
                )
        elif event_type in {"conversation.closed.v1", "conversation.updated.v1"}:
            row = await db.scalar(
                select(ConversationProjection).where(ConversationProjection.id == conversation_id)
            )
            if row and event_type == "conversation.closed.v1":
                row.status = "CLOSED"
        elif event_type.startswith("conversation.member_"):
            member_id = UUID(str(payload["member_id"]))
            row = await db.scalar(
                select(ConversationMemberProjection).where(
                    ConversationMemberProjection.conversation_id == conversation_id,
                    ConversationMemberProjection.member_id == member_id,
                )
            )
            if row:
                row.status = "ACTIVE" if event_type == "conversation.member_added.v1" else "REMOVED"
    db.add(ProcessedEvent(event_id=event_id, event_type=event_type, producer=envelope["producer"]))
    return True


def consumer_callback(channel, method, _properties, body):
    async def process():
        async with SessionLocal.begin() as db:
            await apply_projection(db, json.loads(body))

    try:
        asyncio.run(process())
    except Exception:
        channel.basic_nack(method.delivery_tag, requeue=True)
    else:
        channel.basic_ack(method.delivery_tag)


class Publisher:
    def __enter__(self):
        self.connection = pika.BlockingConnection(pika.URLParameters(settings().rabbitmq_url))
        self.channel = self.connection.channel()
        self.channel.exchange_declare(
            exchange="messaging.events", exchange_type="topic", durable=True
        )
        self.channel.confirm_delivery()
        return self

    def publish(self, event):
        body = {
            "event_id": str(event.event_id),
            "event_type": event.event_type,
            "event_version": 1,
            "occurred_at": event.created_at.isoformat(),
            "producer": "messaging-service",
            "organization_id": str(event.organization_id),
            "aggregate_id": str(event.aggregate_id),
            "correlation_id": event.correlation_id,
            "payload": event.payload,
        }
        self.channel.basic_publish(
            exchange="messaging.events",
            routing_key=event.event_type,
            body=json.dumps(body).encode(),
            mandatory=True,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,
                message_id=str(event.event_id),
                correlation_id=event.correlation_id,
            ),
        )

    def __exit__(self, *_):
        self.connection.close()


async def publish_one(publisher: Publisher) -> bool:
    async with SessionLocal.begin() as db:
        event = await db.scalar(
            select(OutboxEvent)
            .where(OutboxEvent.status == "PENDING")
            .order_by(OutboxEvent.created_at)
            .with_for_update(skip_locked=True)
            .limit(1)
        )
        if event is None:
            return False
        event.status = "PROCESSING"
        try:
            await asyncio.to_thread(publisher.publish, event)
        except Exception as exc:
            event.retry_count += 1
            event.status = "FAILED" if event.retry_count >= 10 else "PENDING"
            event.last_error = type(exc).__name__
        else:
            event.status = "PUBLISHED"
            event.published_at = datetime.now(UTC)
    return True
