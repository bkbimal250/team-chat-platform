from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DomainError
from app.models import (
    BlockProjection,
    ConversationMemberProjection,
    ConversationProjection,
    ConversationReadState,
    ConversationSequence,
    Message,
    OutboxEvent,
)
from app.security import Principal


async def authorize(db: AsyncSession, p: Principal, conversation_id: UUID):
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
        if peer_ids:
            blocked = await db.scalar(
                select(BlockProjection).where(
                    (
                        (BlockProjection.blocker_user_id == p.user_id)
                        & (BlockProjection.blocked_user_id.in_(peer_ids))
                    )
                    | (
                        (BlockProjection.blocked_user_id == p.user_id)
                        & (BlockProjection.blocker_user_id.in_(peer_ids))
                    )
                )
            )
            if blocked:
                raise DomainError(
                    "DIRECT_CONVERSATION_BLOCKED", "Direct messaging is unavailable.", 403
                )
    return conversation


def event(message: Message, event_type: str, correlation_id: str, **extra):
    payload = {
        "message_id": str(message.id),
        "organization_id": str(message.organization_id),
        "conversation_id": str(message.conversation_id),
        "sender_user_id": str(message.sender_user_id),
        "sender_member_id": str(message.sender_member_id),
        "sender_device_id": str(message.sender_device_id),
        "type": message.type,
        "text": message.text,
        "reply_to_message_id": str(message.reply_to_message_id)
        if message.reply_to_message_id
        else None,
        "client_message_id": str(message.client_message_id),
        "sequence": message.sequence,
        "created_at": message.created_at.isoformat() if message.created_at else None,
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
    if body.type != "TEXT":
        raise DomainError("MESSAGE_TYPE_UNSUPPORTED", "Only TEXT messages may be sent.", 400)
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
    if body.reply_to_message_id:
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
        type=body.type,
        text=body.text,
        reply_to_message_id=body.reply_to_message_id,
        client_message_id=body.client_message_id,
        sequence=sequence,
    )
    db.add(message)
    await db.flush()
    db.add(event(message, "message.created.v1", correlation_id))
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
        )
        db.add(state)
    if read:
        if sequence > state.last_delivered_sequence:
            raise DomainError("READ_INVALID", "Read cannot exceed delivery.", 400)
        state.last_read_sequence = max(state.last_read_sequence, sequence)
    else:
        state.last_delivered_sequence = max(state.last_delivered_sequence, sequence)
    db.add(
        OutboxEvent(
            event_type="message.read.v1" if read else "message.delivered.v1",
            aggregate_id=conversation_id,
            organization_id=p.organization_id,
            correlation_id=correlation_id,
            payload={
                "organization_id": str(p.organization_id),
                "conversation_id": str(conversation_id),
                "member_id": str(p.member_id),
                "sequence": sequence,
            },
        )
    )
    return state
