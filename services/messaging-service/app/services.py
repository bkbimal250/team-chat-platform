from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DomainError, settings
from app.models import (
    BlockProjection,
    ConversationMemberProjection,
    ConversationProjection,
    ConversationReadState,
    ConversationSequence,
    MediaProjection,
    Message,
    OrganizationMemberProjection,
    OutboxEvent,
)
from app.security import Principal


async def resolve_contact_identity(actor: UUID, contact_id: UUID) -> UUID:
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            response = await client.post(
                settings().user_service_url.rstrip("/") + "/internal/v1/contacts/authorize",
                headers={"X-Internal-Service-Token": settings().internal_service_token},
                json={"identity_id": str(actor), "contact_id": str(contact_id)},
            )
        if response.status_code in {403, 404}:
            raise DomainError("CONTACT_UNAVAILABLE", "Contact is unavailable.", 404)
        response.raise_for_status()
        return UUID(response.json()["identity_id"])
    except DomainError:
        raise
    except (httpx.HTTPError, ValueError, KeyError):
        raise DomainError(
            "CONTACT_UNAVAILABLE", "Contact authorization is unavailable.", 503
        ) from None


async def blocked_between(db: AsyncSession, user_a: UUID, user_b: UUID) -> bool:
    if user_a == user_b:
        return False
    blocked = await db.scalar(
        select(BlockProjection.id).where(
            (
                (BlockProjection.blocker_user_id == user_a)
                & (BlockProjection.blocked_user_id == user_b)
            )
            | (
                (BlockProjection.blocker_user_id == user_b)
                & (BlockProjection.blocked_user_id == user_a)
            )
        )
    )
    return bool(blocked)


async def ensure_org_member_active(db: AsyncSession, p: Principal):
    if p.organization_id is None:
        return
    row = await db.scalar(
        select(OrganizationMemberProjection).where(
            OrganizationMemberProjection.organization_id == p.organization_id,
            OrganizationMemberProjection.member_id == p.member_id,
            OrganizationMemberProjection.status == "ACTIVE",
        )
    )
    if row is None:
        raise DomainError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.", 403)


async def authorize(db: AsyncSession, p: Principal, conversation_id: UUID):
    await ensure_org_member_active(db, p)
    if p.organization_id is None:
        try:
            async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
                response = await client.post(
                    settings().conversation_service_url.rstrip("/")
                    + f"/internal/v1/conversations/{conversation_id}/authorize",
                    headers={"X-Internal-Service-Token": settings().internal_service_token},
                    json={
                        "organization_id": None,
                        "member_id": str(p.member_id),
                        "identity_id": str(p.user_id),
                    },
                )
            response.raise_for_status()
            data = response.json()
            if (
                data.get("allowed") is not True
                or data.get("organization_id") is not None
                or data.get("conversation_id") != str(conversation_id)
                or data.get("member_id") != str(p.user_id)
            ):
                raise DomainError(
                    "CONVERSATION_FORBIDDEN", "Conversation access is unavailable.", 403
                )
        except (httpx.HTTPError, ValueError):
            raise DomainError(
                "CONVERSATION_FORBIDDEN", "Conversation access is unavailable.", 403
            ) from None
        return None
    conversation = await db.scalar(
        select(ConversationProjection).where(
            ConversationProjection.id == conversation_id,
            ConversationProjection.organization_id == p.organization_id,
        )
    )
    member = await db.scalar(
        select(ConversationMemberProjection).where(
            ConversationMemberProjection.conversation_id == conversation_id,
            ConversationMemberProjection.organization_id == p.organization_id,
            ConversationMemberProjection.member_id == p.member_id,
        )
    )
    if (
        not conversation
        or conversation.status != "ACTIVE"
        or not member
        or member.status != "ACTIVE"
    ):
        raise DomainError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.", 403)
    if conversation.type == "DIRECT":
        peers = list(
            (
                await db.scalars(
                    select(ConversationMemberProjection).where(
                        ConversationMemberProjection.conversation_id == conversation_id,
                        ConversationMemberProjection.organization_id == p.organization_id,
                        ConversationMemberProjection.status == "ACTIVE",
                    )
                )
            ).all()
        )
        peer_ids = [row.user_id for row in peers if row.user_id != p.user_id]
        if peer_ids and await blocked_between(db, p.user_id, peer_ids[0]):
            raise DomainError(
                "DIRECT_CONVERSATION_BLOCKED", "Direct messaging is unavailable.", 403
            )
    return conversation


def event(message: Message, event_type: str, correlation_id: str, **extra):
    payload = {
        "message_id": str(message.id),
        "organization_id": str(message.organization_id) if message.organization_id else None,
        "conversation_id": str(message.conversation_id),
        "sender_user_id": str(message.sender_user_id),
        "sender_member_id": str(message.sender_member_id),
        "sender_device_id": str(message.sender_device_id),
        "type": message.type,
        "text": message.text,
        "e2ee": getattr(message, "e2ee_envelope", None),
        "attachment": getattr(message, "attachment", None),
        "media_id": (getattr(message, "attachment", None) or {}).get("media_id"),
        "reply_to_message_id": str(message.reply_to_message_id)
        if message.reply_to_message_id
        else None,
        "forward_from_message_id": str(message.forward_from_message_id)
        if getattr(message, "forward_from_message_id", None)
        else None,
        "forward_from_conversation_id": str(message.forward_from_conversation_id)
        if getattr(message, "forward_from_conversation_id", None)
        else None,
        "client_message_id": str(message.client_message_id),
        "sequence": message.sequence,
        "created_at": message.created_at.isoformat() if message.created_at else None,
        "version_at": (
            getattr(message, "deleted_at", None)
            or getattr(message, "edited_at", None)
            or message.created_at
        ).isoformat()
        if message.created_at
        else None,
    }
    payload.update(extra)
    return OutboxEvent(
        event_type=event_type,
        aggregate_id=message.id,
        organization_id=message.organization_id,
        correlation_id=correlation_id,
        payload=payload,
    )


async def send(db: AsyncSession, p: Principal, conversation_id: UUID, body, correlation_id: str):
    await authorize(db, p, conversation_id)
    if body.type not in {"TEXT", "E2EE", "IMAGE", "VIDEO", "AUDIO", "VOICE", "DOCUMENT"}:
        raise DomainError("MESSAGE_TYPE_UNSUPPORTED", "Message type is unsupported.", 400)

    existing = await db.scalar(
        select(Message).where(
            Message.organization_id == p.organization_id,
            Message.conversation_id == conversation_id,
            Message.sender_device_id == p.device_id,
            Message.client_message_id == body.client_message_id,
        )
    )
    if existing:
        return existing

    forward_from_message_id = None
    forward_from_conversation_id = None
    message_type = body.type
    message_text = body.text
    e2ee_envelope = None
    attachment = None

    if body.type == "E2EE":
        e2ee_envelope = body.e2ee.model_dump(mode="json")
        message_text = None
    elif body.forward_from_message_id:
        source = await db.scalar(
            select(Message).where(
                Message.id == body.forward_from_message_id,
                Message.organization_id == p.organization_id,
                Message.deleted_at.is_(None),
            )
        )
        if not source:
            raise DomainError("FORWARD_INVALID", "Forward source is unavailable.", 400)
        await authorize(db, p, source.conversation_id)
        forward_from_message_id = source.id
        forward_from_conversation_id = source.conversation_id
        message_type = source.type
        message_text = body.text or source.text
        attachment = source.attachment
        if message_type == "TEXT" and (not message_text or not str(message_text).strip()):
            raise DomainError("FORWARD_INVALID", "Forward source is unavailable.", 400)
    elif body.reply_to_message_id:
        reply = await db.scalar(
            select(Message).where(
                Message.id == body.reply_to_message_id,
                Message.organization_id == p.organization_id,
                Message.conversation_id == conversation_id,
                Message.deleted_at.is_(None),
            )
        )
        if not reply:
            raise DomainError("REPLY_INVALID", "Reply target is unavailable.", 400)
    elif body.type != "TEXT":
        attachment = await media_attachment(db, p, conversation_id, body)

    counter = await db.scalar(
        select(ConversationSequence)
        .where(ConversationSequence.conversation_id == conversation_id)
        .with_for_update()
    )
    if counter is None:
        counter = ConversationSequence(conversation_id=conversation_id, next_sequence=1)
        db.add(counter)
        await db.flush()
    sequence = counter.next_sequence
    counter.next_sequence += 1
    message = Message(
        organization_id=p.organization_id,
        conversation_id=conversation_id,
        sender_user_id=p.user_id,
        sender_member_id=p.member_id,
        sender_device_id=p.device_id,
        type=message_type,
        text=message_text,
        e2ee_envelope=e2ee_envelope,
        attachment=attachment,
        reply_to_message_id=body.reply_to_message_id,
        forward_from_message_id=forward_from_message_id,
        forward_from_conversation_id=forward_from_conversation_id,
        client_message_id=body.client_message_id,
        sequence=sequence,
    )
    db.add(message)
    await db.flush()
    mention_extra = {}
    if body.mentioned_member_ids:
        mention_extra["mentioned_member_ids"] = [
            str(member_id) for member_id in body.mentioned_member_ids
        ]
    db.add(event(message, "message.created.v1", correlation_id, **mention_extra))
    return message


async def mark(db, p, conversation_id, sequence, read, correlation_id):
    await authorize(db, p, conversation_id)
    state = await db.scalar(
        select(ConversationReadState)
        .where(
            ConversationReadState.organization_id == p.organization_id,
            ConversationReadState.conversation_id == conversation_id,
            ConversationReadState.member_id == p.member_id,
        )
        .with_for_update()
    )
    if state is None:
        state = ConversationReadState(
            organization_id=p.organization_id,
            conversation_id=conversation_id,
            member_id=p.member_id,
            last_delivered_sequence=0,
            last_read_sequence=0,
        )
        db.add(state)
    if read:
        if sequence > (state.last_delivered_sequence or 0):
            raise DomainError("READ_INVALID", "Read cannot exceed delivery.", 400)
        state.last_read_sequence = max(state.last_read_sequence or 0, sequence)
    else:
        state.last_delivered_sequence = max(state.last_delivered_sequence or 0, sequence)
    db.add(
        OutboxEvent(
            event_type="message.read.v1" if read else "message.delivered.v1",
            aggregate_id=conversation_id,
            organization_id=p.organization_id,
            correlation_id=correlation_id,
            payload={
                "organization_id": str(p.organization_id) if p.organization_id else None,
                "conversation_id": str(conversation_id),
                "member_id": str(p.member_id),
                "sequence": sequence,
            },
        )
    )
    return state


async def media_attachment(db, p, conversation_id, body):
    if body.type == "TEXT":
        return None
    media = await db.get(MediaProjection, body.media_id)
    if (
        not media
        or media.organization_id != p.organization_id
        or media.conversation_id != conversation_id
        or media.uploader_member_id != p.member_id
    ):
        raise DomainError(
            "MEDIA_UNAVAILABLE", "Attachment is unavailable for this conversation.", 403
        )
    if media.status != "READY":
        raise DomainError("MEDIA_NOT_READY", "Attachment is not ready. Try again shortly.", 409)
    expected = "audio" if body.type == "VOICE" else body.type.lower()
    if media.metadata_json["media_type"] != expected:
        raise DomainError("MEDIA_TYPE_MISMATCH", "Attachment type does not match.", 422)
    return {"media_id": str(media.id), **media.metadata_json}
