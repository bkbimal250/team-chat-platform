"""Durable, tenant-scoped message summaries owned by Conversation Service."""

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select

from app.models import Conversation, ConversationMessageProjection, ConversationReadProjection


def stamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


async def project_message(db, event):
    payload, kind = event["payload"], event["event_type"]
    if kind == "conversation.summary.message.v1":
        kind = payload["source_kind"]
    elif kind == "conversation.summary.read.v1":
        kind = "message.read.v1"
    org = UUID(str(event["organization_id"])) if event.get("organization_id") else None
    cid = UUID(payload["conversation_id"])
    if (
        "organization_id" in payload
        and (UUID(payload["organization_id"]) if payload["organization_id"] else None) != org
    ):
        raise ValueError("Message tenant mismatch")
    conversation = await db.scalar(
        select(Conversation)
        .where(Conversation.id == cid, Conversation.organization_id == org)
        .with_for_update()
    )
    if conversation is None:
        raise ValueError("Conversation projection is not ready")
    if kind == "message.read.v1":
        member = UUID(payload["member_id"])
        row = await db.get(ConversationReadProjection, (cid, member))
        if row is None:
            db.add(
                ConversationReadProjection(
                    organization_id=org,
                    conversation_id=cid,
                    member_id=member,
                    sequence=payload["sequence"],
                )
            )
        else:
            row.sequence = max(row.sequence, payload["sequence"])
        return
    if kind not in {"message.created.v1", "message.edited.v1", "message.deleted.v1"}:
        return
    message_id = UUID(payload["message_id"])
    row = await db.get(ConversationMessageProjection, message_id)
    version = stamp(payload.get("version_at") or event.get("occurred_at") or payload["created_at"])
    if row is not None and (row.organization_id != org or row.conversation_id != cid):
        raise ValueError("Message identity mismatch")
    # Tombstones are permanent; late create/edit events cannot revive a deleted message.
    if row is not None and (row.is_deleted or version < row.version_at.replace(tzinfo=UTC)):
        return
    values = dict(
        organization_id=org,
        conversation_id=cid,
        sender_member_id=UUID(payload["sender_member_id"]),
        sequence=payload["sequence"],
        preview=(
            payload.get("text")
            or {
                "IMAGE": "Image",
                "VIDEO": "Video",
                "AUDIO": "Audio",
                "VOICE": "Voice note",
                "DOCUMENT": "Document",
            }.get(payload.get("type"), "")
        )[:200]
        or None,
        created_at=stamp(payload["created_at"]),
        version_at=version,
        is_deleted=kind == "message.deleted.v1",
    )
    if row is None:
        db.add(ConversationMessageProjection(message_id=message_id, **values))
    else:
        for key, value in values.items():
            setattr(row, key, value)


async def summaries(db, organization_id, member_id, conversation_ids):
    """Two batched queries, independent of the number of visible conversations."""
    if not conversation_ids:
        return {}
    message = ConversationMessageProjection
    latest = (
        select(message.conversation_id, func.max(message.sequence).label("sequence"))
        .where(
            message.organization_id == organization_id,
            message.conversation_id.in_(conversation_ids),
            message.is_deleted.is_(False),
        )
        .group_by(message.conversation_id)
        .subquery()
    )
    previews = (
        (
            await db.execute(
                select(message)
                .join(
                    latest,
                    (message.conversation_id == latest.c.conversation_id)
                    & (message.sequence == latest.c.sequence),
                )
                .where(message.organization_id == organization_id)
            )
        )
        .scalars()
        .all()
    )
    read = ConversationReadProjection
    unread = (
        await db.execute(
            select(message.conversation_id, func.count())
            .outerjoin(
                read,
                (read.organization_id.is_not_distinct_from(message.organization_id))
                & (read.conversation_id == message.conversation_id)
                & (read.member_id == member_id),
            )
            .where(
                message.organization_id == organization_id,
                message.conversation_id.in_(conversation_ids),
                message.is_deleted.is_(False),
                message.sender_member_id != member_id,
                message.sequence > func.coalesce(read.sequence, 0),
            )
            .group_by(message.conversation_id)
        )
    ).all()
    result = {
        cid: {
            "last_message_preview": None,
            "last_message_at": None,
            "last_message_sequence": None,
            "unread_count": 0,
        }
        for cid in conversation_ids
    }
    for row in previews:
        result[row.conversation_id].update(
            last_message_preview=row.preview,
            last_message_at=row.created_at,
            last_message_sequence=row.sequence,
        )
    for cid, count in unread:
        result[cid]["unread_count"] = count
    return result
