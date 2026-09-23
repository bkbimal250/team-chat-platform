"""Idempotent Organization-event projection handler.

The RabbitMQ adapter must ACK only after this coroutine's transaction commits.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import MembershipProjection, ProcessedEvent


async def apply_membership_event(db: AsyncSession, envelope: dict) -> bool:
    event_id = UUID(envelope["event_id"])
    exists = await db.scalar(select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id))
    if exists:
        return False
    payload = envelope["payload"]
    event_type = envelope["event_type"]
    if event_type.startswith("member."):
        organization_id = UUID(str(envelope["organization_id"]))
        member_id = UUID(str(payload["member_id"]))
        projection = await db.scalar(
            select(MembershipProjection).where(
                MembershipProjection.organization_id == organization_id,
                MembershipProjection.member_id == member_id,
            )
        )
        if projection is None:
            projection = MembershipProjection(
                organization_id=organization_id,
                member_id=member_id,
                identity_id=UUID(str(payload["identity_id"])),
                status=payload.get("status", event_type.split(".")[1].upper()),
            )
            db.add(projection)
        else:
            projection.status = payload.get("status", event_type.split(".")[1].upper())
    elif event_type == "organization.suspended.v1":
        organization_id = UUID(str(envelope["organization_id"]))
        for projection in await db.scalars(
            select(MembershipProjection).where(
                MembershipProjection.organization_id == organization_id
            )
        ):
            projection.status = "SUSPENDED"
    db.add(ProcessedEvent(event_id=event_id, event_type=event_type, producer=envelope["producer"]))
    return True
