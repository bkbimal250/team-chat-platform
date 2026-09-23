"""Transactional outbox publisher; caller supplies a confirming broker adapter."""

from datetime import UTC, datetime

from sqlalchemy import select

from app.db import Sessions
from app.models import OutboxEvent


async def publish_pending(broker, batch_size: int = 50) -> int:
    published = 0
    async with Sessions.begin() as db:
        events = (
            await db.scalars(
                select(OutboxEvent)
                .where(OutboxEvent.status == "PENDING")
                .with_for_update(skip_locked=True)
                .limit(batch_size)
            )
        ).all()
        for event in events:
            try:
                await broker.publish(event)  # publish() returns only after publisher confirmation
                event.status, event.published_at = "PUBLISHED", datetime.now(UTC)
                published += 1
            except Exception as exc:
                event.retry_count += 1
                event.last_error = type(exc).__name__
    return published
