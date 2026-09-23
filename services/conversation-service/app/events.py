"""Idempotent projection handlers; broker ACK happens after their transaction."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import BlockProjection, MemberProjection, ProcessedEvent


async def consume(db: AsyncSession, event: dict) -> bool:
    event_id = uuid.UUID(str(event["event_id"]))
    if await db.scalar(select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)):
        return False
    kind, payload = event["event_type"], event["payload"]
    if kind.startswith("member."):
        org, member = uuid.UUID(str(event["organization_id"])), uuid.UUID(str(payload["member_id"]))
        projection = await db.scalar(
            select(MemberProjection).where(
                MemberProjection.organization_id == org, MemberProjection.member_id == member
            )
        )
        if projection is None:
            projection = MemberProjection(
                organization_id=org,
                member_id=member,
                user_id=uuid.UUID(str(payload["user_id"])) if payload.get("user_id") else None,
                status=payload.get("status", kind.split(".")[1].upper()),
            )
            db.add(projection)
        else:
            projection.status = payload.get("status", kind.split(".")[1].upper())
    elif kind == "user.blocked.v1":
        db.add(
            BlockProjection(
                blocker_user_id=uuid.UUID(str(payload["blocker_user_id"])),
                blocked_user_id=uuid.UUID(str(payload["blocked_user_id"])),
            )
        )
    elif kind == "user.unblocked.v1":
        row = await db.scalar(
            select(BlockProjection).where(
                BlockProjection.blocker_user_id == uuid.UUID(str(payload["blocker_user_id"])),
                BlockProjection.blocked_user_id == uuid.UUID(str(payload["blocked_user_id"])),
            )
        )
        if row:
            await db.delete(row)
    db.add(ProcessedEvent(event_id=event_id, event_type=kind, producer=event["producer"]))
    return True
