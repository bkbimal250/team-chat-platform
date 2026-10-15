from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Message, MessageReaction


async def reactions_for_messages(db: AsyncSession, message_ids: list[UUID]) -> dict[UUID, list[dict]]:
    if not message_ids:
        return {}
    rows = (
        await db.scalars(
            select(MessageReaction).where(MessageReaction.message_id.in_(message_ids))
        )
    ).all()
    grouped: dict[UUID, list[dict]] = {}
    for row in rows:
        grouped.setdefault(row.message_id, []).append(
            {
                "member_id": str(row.member_id),
                "user_id": str(row.user_id),
                "reaction": row.reaction,
                "created_at": row.created_at.isoformat() if row.created_at else None,
            }
        )
    return grouped


def message_view(message: Message, reactions: list[dict] | None = None) -> dict:
    if message.deleted_at or message.status == "DELETED":
        return {
            "id": str(message.id),
            "organization_id": str(message.organization_id) if message.organization_id else None,
            "conversation_id": str(message.conversation_id),
            "sender_member_id": str(message.sender_member_id),
            "sequence": message.sequence,
            "status": "DELETED",
            "deleted_at": message.deleted_at.isoformat() if message.deleted_at else None,
            "reactions": reactions or [],
        }
    payload = {
        "id": str(message.id),
        "organization_id": str(message.organization_id) if message.organization_id else None,
        "conversation_id": str(message.conversation_id),
        "sender_user_id": str(message.sender_user_id),
        "sender_member_id": str(message.sender_member_id),
        "sender_device_id": str(message.sender_device_id),
        "type": message.type,
        "text": message.text if message.type != "E2EE" else None,
        "e2ee": message.e2ee_envelope,
        "attachment": message.attachment,
        "reply_to_message_id": str(message.reply_to_message_id)
        if message.reply_to_message_id
        else None,
        "forward_from_message_id": str(message.forward_from_message_id)
        if message.forward_from_message_id
        else None,
        "forward_from_conversation_id": str(message.forward_from_conversation_id)
        if message.forward_from_conversation_id
        else None,
        "client_message_id": str(message.client_message_id),
        "sequence": message.sequence,
        "status": message.status,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "edited_at": message.edited_at.isoformat() if message.edited_at else None,
        "reactions": reactions or [],
    }
    return payload
