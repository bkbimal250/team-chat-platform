"""Idempotent projection handlers; broker ACK happens after their transaction."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chat_projection import project_message
from app.models import BlockProjection, MemberProjection, MStatus, ProcessedEvent
from app.services import ConversationService


def _member_status(kind: str, payload: dict) -> str:
    if payload.get("status"):
        return str(payload["status"]).upper()
    action = kind.split(".")[1].upper()
    return action


async def consume(db: AsyncSession, event: dict) -> bool:
    event_id = uuid.UUID(str(event["event_id"]))
    if await db.scalar(select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)):
        return False
    kind, payload = event["event_type"], event["payload"]
    correlation = str(event.get("correlation_id") or "")
    if kind.startswith("message.") or kind.startswith("conversation.summary."):
        await project_message(db, event)
    elif kind.startswith("member."):
        org, member = uuid.UUID(str(event["organization_id"])), uuid.UUID(str(payload["member_id"]))
        status = _member_status(kind, payload)
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
                status=status,
            )
            db.add(projection)
        else:
            projection.status = status
            if payload.get("user_id"):
                projection.user_id = uuid.UUID(str(payload["user_id"]))
        if kind in {"member.left.v2", "member.removed.v2"}:
            await ConversationService().revoke_org_conversations(
                db,
                org,
                member,
                MStatus.LEFT if kind == "member.left.v2" else MStatus.REMOVED,
                correlation,
            )
    elif kind == "user.blocked.v1":
        db.add(
            BlockProjection(
                blocker_user_id=uuid.UUID(
                    str(payload.get("blocker_identity_id", payload["blocker_user_id"]))
                ),
                blocked_user_id=uuid.UUID(
                    str(payload.get("blocked_identity_id", payload["blocked_user_id"]))
                ),
            )
        )
    elif kind == "user.unblocked.v1":
        row = await db.scalar(
            select(BlockProjection).where(
                BlockProjection.blocker_user_id
                == uuid.UUID(str(payload.get("blocker_identity_id", payload["blocker_user_id"]))),
                BlockProjection.blocked_user_id
                == uuid.UUID(str(payload.get("blocked_identity_id", payload["blocked_user_id"]))),
            )
        )
        if row:
            await db.delete(row)
    db.add(ProcessedEvent(event_id=event_id, event_type=kind, producer=event["producer"]))
    return True
