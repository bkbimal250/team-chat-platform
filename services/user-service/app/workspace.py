"""Company workspace directory: tenant-scoped people search separate from personal contacts."""

import uuid

from fastapi import HTTPException, Request
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import AuthContext
from app.config import get_settings
from app.main import MembershipProjection, User, UserPrivacySettings, active_avatar

WORKSPACE_DIRECTORY_VISIBILITY = frozenset({"EVERYONE", "ORGANIZATION"})


def workspace_directory_visible(privacy: UserPrivacySettings) -> bool:
    return (
        privacy.profile_photo_visibility in WORKSPACE_DIRECTORY_VISIBILITY
        or privacy.about_visibility in WORKSPACE_DIRECTORY_VISIBILITY
    )


def workspace_profile(user: User, privacy: UserPrivacySettings) -> dict:
    return {
        "user_id": str(user.id),
        "display_name": user.display_name,
        "avatar_media_id": (
            str(active_avatar(user))
            if active_avatar(user)
            and privacy.profile_photo_visibility in WORKSPACE_DIRECTORY_VISIBILITY
            else None
        ),
        "about": (
            user.about
            if user.about and privacy.about_visibility in WORKSPACE_DIRECTORY_VISIBILITY
            else None
        ),
        "status": user.status,
    }


def membership_user_join():
    return or_(
        MembershipProjection.user_id == User.id,
        and_(
            MembershipProjection.user_id.is_(None),
            MembershipProjection.identity_id == User.identity_id,
        ),
    )


async def require_active_workspace_member(
    session: AsyncSession, context: AuthContext
) -> MembershipProjection:
    if context.organization_id is None or context.member_id is None:
        raise HTTPException(
            403, "Workspace membership is required; personal contact discovery is unavailable."
        )
    row = await session.scalar(
        select(MembershipProjection).where(
            MembershipProjection.organization_id == context.organization_id,
            MembershipProjection.member_id == context.member_id,
            MembershipProjection.identity_id == context.identity_id,
            MembershipProjection.status == "ACTIVE",
        )
    )
    if row is None:
        raise HTTPException(403, "Workspace membership is unavailable.")
    return row


async def workspace_search_rate_limit(request: Request, identity_id: uuid.UUID) -> None:
    redis = request.app.state.contact_redis
    settings = get_settings()
    ip = request.client.host if request.client else "unknown"
    keys = [
        f"workspace:search:identity:{identity_id}",
        f"workspace:search:ip:{ip}",
    ]
    limit = settings.WORKSPACE_SEARCH_RATE_LIMIT
    window = settings.WORKSPACE_SEARCH_RATE_WINDOW_SECONDS
    script = """
for i,key in ipairs(KEYS) do
 if tonumber(redis.call('GET',key) or '0') + 1 > tonumber(ARGV[1]) then
  return math.max(1, redis.call('TTL', key))
 end
end
for i,key in ipairs(KEYS) do
 local value = redis.call('INCR', key)
 if value == 1 then redis.call('EXPIRE', key, ARGV[2]) end
end
return 0
"""
    try:
        retry = await redis.eval(script, len(keys), *keys, limit, window)
    except Exception:
        raise HTTPException(503, "Workspace search is temporarily unavailable.") from None
    if retry:
        raise HTTPException(
            429,
            "Too many workspace searches. Please try again later.",
            headers={"Retry-After": str(retry)},
        )
