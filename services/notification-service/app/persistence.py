"""PostgreSQL transaction boundary used by Rabbit consumers in production."""

from uuid import UUID

from sqlalchemy import select

from app.models import OutboxEvent, ProcessedEvent


class NotificationRepository:
    def __init__(self, session):
        self.session = session

    async def process_event(self, event, apply):
        async with self.session.begin():
            event_id = UUID(event["event_id"])
            existing = (
                await self.session.execute(
                    select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)
                )
            ).scalar_one_or_none()
            if existing:
                return False
            await apply(self.session)
            self.session.add(ProcessedEvent(event_id=event_id))
        return True

    async def pending_outbox(self, limit=100):
        result = await self.session.execute(
            select(OutboxEvent).where(OutboxEvent.status == "PENDING").limit(limit)
        )
        return list(result.scalars())
