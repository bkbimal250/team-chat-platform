"""Keep membership projections aligned with durable user profiles."""

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession


async def link_user_to_projections(db: AsyncSession, identity_id: uuid.UUID, user_id: uuid.UUID) -> None:
    from app.main import MembershipProjection
    rows = (
        await db.scalars(
            select(MembershipProjection).where(
                MembershipProjection.identity_id == identity_id,
                or_(
                    MembershipProjection.user_id.is_(None),
                    MembershipProjection.user_id != user_id,
                ),
            )
        )
    ).all()
    for row in rows:
        row.user_id = user_id


async def resolve_user_for_identity(db: AsyncSession, reference: uuid.UUID):
    from app.main import User

    return await db.scalar(
        select(User).where(or_(User.id == reference, User.identity_id == reference))
    )
