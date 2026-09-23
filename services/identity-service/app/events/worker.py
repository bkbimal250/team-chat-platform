import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.db.session import SessionLocal
from app.events.publisher import RabbitPublisher
from app.models.models import OutboxEvent, OutboxStatus


async def publish_one(publisher: RabbitPublisher) -> bool:
    async with SessionLocal.begin() as db:
        event = (
            await db.execute(
                select(OutboxEvent)
                .where(
                    OutboxEvent.status == OutboxStatus.PENDING,
                    OutboxEvent.available_at <= datetime.now(UTC),
                )
                .order_by(OutboxEvent.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
        ).scalar_one_or_none()
        if event is None:
            return False
        event.status = OutboxStatus.PROCESSING
        try:
            await asyncio.to_thread(publisher.publish, event)
        except Exception as exc:
            event.retry_count += 1
            event.status = OutboxStatus.FAILED if event.retry_count >= 10 else OutboxStatus.PENDING
            event.available_at = datetime.now(UTC) + timedelta(
                seconds=min(2**event.retry_count, 3600)
            )
            event.last_error = type(exc).__name__
        else:
            event.status, event.published_at = OutboxStatus.PUBLISHED, datetime.now(UTC)
    return True


async def run() -> None:
    while True:
        try:
            with RabbitPublisher() as publisher:
                while await publish_one(publisher):
                    pass
        except Exception:
            pass
        await asyncio.sleep(2)
