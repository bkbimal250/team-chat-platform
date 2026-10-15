"""Transactional event handlers; the broker adapter ACKs only after commit."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.membership_projection import link_user_to_projections, resolve_user_for_identity
from app.main import (
    MembershipProjection,
    OutboxEvent,
    ProcessedEvent,
    User,
    UserPreferences,
    UserPrivacySettings,
)


async def consume(db: AsyncSession, event: dict) -> bool:
    event_id = uuid.UUID(str(event["event_id"]))
    if await db.scalar(select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)):
        return False
    event_type, payload = event["event_type"], event["payload"]
    if event_type == "identity.created.v1":
        identity_id = uuid.UUID(str(payload.get("identity_id", payload.get("resource_id"))))
        user = await db.scalar(select(User).where(User.identity_id == identity_id))
        if user is None:
            user = User(identity_id=identity_id, display_name=payload.get("display_name", ""))
            db.add(user)
            await db.flush()
            db.add_all([UserPreferences(user_id=user.id), UserPrivacySettings(user_id=user.id)])
            db.add(
                OutboxEvent(
                    event_type="user.created.v1",
                    aggregate_id=user.id,
                    correlation_id=event.get("correlation_id", ""),
                    payload={"user_id": str(user.id), "identity_id": str(user.identity_id)},
                    organization_id=None,
                )
            )
        await link_user_to_projections(db, user.identity_id, user.id)
    elif event_type.startswith("member."):
        organization_id = uuid.UUID(str(event["organization_id"]))
        member_id = uuid.UUID(str(payload["member_id"]))
        row = await db.scalar(
            select(MembershipProjection).where(
                MembershipProjection.organization_id == organization_id,
                MembershipProjection.member_id == member_id,
            )
        )
        status = payload.get("status", event_type.split(".")[1].upper())
        reference = payload.get("identity_id", payload.get("user_id"))
        identity_id = uuid.UUID(str(reference)) if reference is not None else None
        user = await resolve_user_for_identity(db, identity_id) if identity_id else None
        if row is None:
            if identity_id is None:
                db.add(
                    ProcessedEvent(
                        event_id=event_id, event_type=event_type, producer=event["producer"]
                    )
                )
                return True
            row = MembershipProjection(
                organization_id=organization_id,
                member_id=member_id,
                identity_id=user.identity_id if user else identity_id,
                user_id=user.id if user else None,
                status=status,
            )
            db.add(row)
        else:
            row.status = status
            if user:
                row.user_id = user.id
                row.identity_id = user.identity_id
            elif identity_id is not None:
                row.identity_id = identity_id
        if user:
            await link_user_to_projections(db, user.identity_id, user.id)
    db.add(ProcessedEvent(event_id=event_id, event_type=event_type, producer=event["producer"]))
    return True
