"""Profile picture duration and privacy are enforced on every read."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext, require_authenticated_context
from app.config import get_settings
from app.main import (
    Contact,
    MembershipProjection,
    User,
    UserBlock,
    UserPrivacySettings,
    active_avatar,
    current_user,
    db,
    outbox,
    projection,
)


class PhotoChoice(BaseModel):
    model_config = ConfigDict(extra="forbid")
    media_id: UUID
    duration_hours: int | None = Field(default=None, ge=1, le=8760, strict=True)


async def resolve_photo(media_id, identity_id, ttl=30):
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=5, follow_redirects=False) as client:
            result = await client.post(
                settings.MEDIA_SERVICE_URL.rstrip("/")
                + f"/internal/v1/media/profile-photos/{media_id}",
                headers={"X-Internal-Service-Token": settings.INTERNAL_SERVICE_TOKEN},
                json={"owner_identity_id": str(identity_id), "ttl": ttl},
            )
        if result.status_code == 404:
            raise HTTPException(404, "Photo unavailable")
        if result.status_code != 200:
            raise HTTPException(503, "Photo storage unavailable")
        return result.json()["download_url"]
    except (httpx.HTTPError, ValueError, KeyError):
        raise HTTPException(503, "Photo storage unavailable") from None


async def visible(session, viewer, owner, request=None, field="profile_photo_visibility"):
    if (
        viewer.status != "ACTIVE"
        or owner.status != "ACTIVE"
        or viewer.deleted_at
        or owner.deleted_at
    ):
        return False
    if viewer.id == owner.id:
        return True
    blocked = await session.scalar(
        select(UserBlock.id).where(
            ((UserBlock.blocker_user_id == viewer.id) & (UserBlock.blocked_user_id == owner.id))
            | ((UserBlock.blocker_user_id == owner.id) & (UserBlock.blocked_user_id == viewer.id))
        )
    )
    if blocked:
        return False
    privacy = await session.get(UserPrivacySettings, owner.id)
    mode = getattr(privacy, field) if privacy else "NOBODY"
    if mode == "EVERYONE":
        return True
    if mode == "CONTACTS" and request is not None:
        from app.contacts import identity_lookup

        # Contact ownership is directional: the profile owner must have saved the viewer.
        digests = list(
            await session.scalars(
                select(Contact.phone_digest).where(Contact.owner_user_id == owner.id)
            )
        )
        for start in range(0, len(digests), 50):
            results = await identity_lookup(request, {"digests": digests[start : start + 50]})
            if any(row.get("identity_id") == str(viewer.identity_id) for row in results):
                return True
        return False
    if mode == "ORGANIZATION":
        organizations = select(MembershipProjection.organization_id).where(
            MembershipProjection.identity_id == viewer.identity_id,
            MembershipProjection.status == "ACTIVE",
        )
        return (
            await session.scalar(
                select(MembershipProjection.id).where(
                    MembershipProjection.identity_id == owner.identity_id,
                    MembershipProjection.status == "ACTIVE",
                    MembershipProjection.organization_id.in_(organizations),
                )
            )
            is not None
        )
    return False


def register_profile_photos(app):
    @app.put("/api/v1/users/me/photo")
    async def set_photo(
        body: PhotoChoice,
        context: AuthContext = Depends(require_authenticated_context),
        session: AsyncSession = Depends(db),
    ):
        async with session.begin():
            user = await current_user(session, context)
            if user.status != "ACTIVE" or user.deleted_at:
                raise HTTPException(403, "Account unavailable")
            await resolve_photo(body.media_id, user.identity_id)
            user.avatar_media_id = body.media_id
            user.avatar_expires_at = (
                (datetime.now(UTC) + timedelta(hours=body.duration_hours))
                if body.duration_hours
                else None
            )
            outbox(session, user, "user.profile_updated.v1")
        return projection(user)

    @app.delete("/api/v1/users/me/photo")
    async def remove_photo(
        context: AuthContext = Depends(require_authenticated_context),
        session: AsyncSession = Depends(db),
    ):
        async with session.begin():
            user = await current_user(session, context)
            user.avatar_media_id = None
            user.avatar_expires_at = None
            outbox(session, user, "user.profile_updated.v1")
        return projection(user)

    @app.get("/api/v1/users/profile-photos/{media_id}")
    async def get_photo(
        media_id: UUID,
        response: Response,
        request: Request,
        context: AuthContext = Depends(require_authenticated_context),
        session: AsyncSession = Depends(db),
    ):
        response.headers["Cache-Control"] = "private, no-store"
        viewer = await current_user(session, context)
        owner = await session.scalar(
            select(User).where(
                User.avatar_media_id == media_id, User.status == "ACTIVE", User.deleted_at.is_(None)
            )
        )
        if (
            viewer.status != "ACTIVE"
            or not owner
            or not active_avatar(owner)
            or not await visible(session, viewer, owner, request)
        ):
            raise HTTPException(404, "Photo unavailable")
        ttl = 30
        if owner.avatar_expires_at:
            ttl = max(
                1, min(ttl, int((owner.avatar_expires_at - datetime.now(UTC)).total_seconds()))
            )
        return {
            "download_url": await resolve_photo(media_id, owner.identity_id, ttl),
            "expires_in": ttl,
            "avatar_expires_at": owner.avatar_expires_at,
        }
