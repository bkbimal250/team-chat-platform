"""Personal broadcast lists: independent per-recipient delivery (not a group conversation)."""

from uuid import UUID, uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import DomainError, settings
from app.models import PersonalBroadcastList, PersonalBroadcastRecipient
from app.schemas import BroadcastListIn, BroadcastRecipientIn, SendMessage
from app.security import Principal
from app.services import blocked_between, resolve_contact_identity, send


async def open_personal_direct(authorization: str, contact_id: UUID) -> UUID:
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            response = await client.post(
                settings().conversation_service_url.rstrip("/")
                + "/api/v1/conversations/personal/direct",
                headers={"Authorization": authorization},
                json={"contact_id": str(contact_id)},
            )
        response.raise_for_status()
        return UUID(response.json()["id"])
    except (httpx.HTTPError, ValueError, KeyError):
        raise DomainError(
            "CONVERSATION_FORBIDDEN", "Conversation access is unavailable.", 403
        ) from None


async def create_list(db: AsyncSession, p: Principal, body: BroadcastListIn) -> PersonalBroadcastList:
    if p.organization_id is not None:
        raise DomainError("PERSONAL_CONTEXT_REQUIRED", "Switch to your personal account.", 403)
    row = PersonalBroadcastList(owner_user_id=p.user_id, title=body.title.strip())
    db.add(row)
    await db.flush()
    return row


async def add_recipient(
    db: AsyncSession, p: Principal, list_id: UUID, body: BroadcastRecipientIn
) -> PersonalBroadcastRecipient:
    if p.organization_id is not None:
        raise DomainError("PERSONAL_CONTEXT_REQUIRED", "Switch to your personal account.", 403)
    broadcast = await db.scalar(
        select(PersonalBroadcastList).where(
            PersonalBroadcastList.id == list_id, PersonalBroadcastList.owner_user_id == p.user_id
        )
    )
    if not broadcast:
        raise DomainError("BROADCAST_NOT_FOUND", "Broadcast list was not found.", 404)
    identity = await resolve_contact_identity(p.user_id, body.contact_id)
    if identity == p.user_id:
        raise DomainError("CONTACT_UNAVAILABLE", "Contact is unavailable.", 404)
    if await blocked_between(db, p.user_id, identity):
        raise DomainError("DIRECT_CONVERSATION_BLOCKED", "Messaging is unavailable.", 403)
    existing = await db.scalar(
        select(PersonalBroadcastRecipient).where(
            PersonalBroadcastRecipient.list_id == list_id,
            PersonalBroadcastRecipient.recipient_identity_id == identity,
        )
    )
    if existing:
        return existing
    row = PersonalBroadcastRecipient(
        list_id=list_id, contact_id=body.contact_id, recipient_identity_id=identity
    )
    db.add(row)
    await db.flush()
    return row


async def fan_out_send(
    db: AsyncSession,
    p: Principal,
    list_id: UUID,
    body: SendMessage,
    authorization: str,
    correlation_id: str,
) -> list[dict]:
    if p.organization_id is not None:
        raise DomainError("PERSONAL_CONTEXT_REQUIRED", "Switch to your personal account.", 403)
    broadcast = await db.scalar(
        select(PersonalBroadcastList).where(
            PersonalBroadcastList.id == list_id, PersonalBroadcastList.owner_user_id == p.user_id
        )
    )
    if not broadcast:
        raise DomainError("BROADCAST_NOT_FOUND", "Broadcast list was not found.", 404)
    recipients = (
        await db.scalars(
            select(PersonalBroadcastRecipient).where(PersonalBroadcastRecipient.list_id == list_id)
        )
    ).all()
    if not recipients:
        raise DomainError("BROADCAST_EMPTY", "Add recipients before sending.", 422)
    deliveries = []
    for recipient in recipients:
        if await blocked_between(db, p.user_id, recipient.recipient_identity_id):
            raise DomainError("DIRECT_CONVERSATION_BLOCKED", "Messaging is unavailable.", 403)
        conversation_id = await open_personal_direct(authorization, recipient.contact_id)
        per_recipient = SendMessage(
            client_message_id=uuid4(),
            type=body.type,
            text=body.text,
            media_id=body.media_id,
            reply_to_message_id=body.reply_to_message_id,
            forward_from_message_id=body.forward_from_message_id,
        )
        message = await send(db, p, conversation_id, per_recipient, correlation_id)
        deliveries.append(
            {
                "conversation_id": str(conversation_id),
                "recipient_identity_id": str(recipient.recipient_identity_id),
                "message_id": str(message.id),
                "sequence": message.sequence,
                "broadcast_list_id": str(list_id),
            }
        )
    return deliveries
