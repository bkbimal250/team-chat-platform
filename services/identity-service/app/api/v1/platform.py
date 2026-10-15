"""Explicit metadata-only platform APIs. Never serialize ORM objects wholesale."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy import String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import command_transaction, get_session
from app.models.models import (
    Device,
    Identity,
    IdentityStatus,
    PlatformAudit,
    PlatformGrant,
    Session,
    SessionStatus,
)
from app.security.dependencies import Principal, current_principal
from app.services.rate_limit import RateLimiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/platform", tags=["platform administration"])
ROLE_PERMISSIONS = {
    "ADMIN": frozenset(
        {
            "platform.access",
            "platform.identities.read",
            "platform.services.read",
            "platform.organizations.read",
        }
    ),
    "SUPER_ADMIN": frozenset(
        {
            "platform.access",
            "platform.identities.read",
            "platform.services.read",
            "platform.organizations.read",
            "platform.sessions.read",
            "platform.sessions.revoke",
            "platform.audit.read",
        }
    ),
}


def grant_permissions(grant, identity):
    if not grant or not grant.active or not identity or identity.status != IdentityStatus.ACTIVE:
        return frozenset()
    return ROLE_PERMISSIONS.get(grant.role, frozenset())


def require(permission: str):
    async def authorize(
        request: Request,
        principal: Principal = Depends(current_principal),
        db: AsyncSession = Depends(get_session),
    ):
        grant = await db.get(PlatformGrant, principal.identity_id)
        identity = await db.get(Identity, principal.identity_id)
        permissions = grant_permissions(grant, identity)
        if permission not in permissions:
            raise DomainError("PLATFORM_FORBIDDEN", "Platform permission is required.", 403)
        await RateLimiter(request.app.state.redis).hit(
            f"platform:read:{principal.identity_id}", 120, 60
        )
        return principal, grant, permissions

    return authorize


@router.get("/me")
async def me(access=Depends(require("platform.access"))):
    principal, grant, permissions = access
    return {
        "identity_id": str(principal.identity_id),
        "role": grant.role,
        "permissions": sorted(permissions),
    }


def identity_metadata(row):
    return {
        "id": row.id,
        "email": row.email,
        "status": row.status,
        "email_verified": row.email_verified,
        "phone_verified": row.phone_verified,
        "created_at": row.created_at,
        "last_login_at": row.last_login_at,
    }


def session_metadata(session, device):
    """Administrative metadata only; credential families and IP/user-agent stay private."""
    return {
        "id": session.id,
        "identity_id": session.identity_id,
        "device_id": session.device_id,
        "device_name": device.device_name if device else None,
        "platform": device.platform if device else None,
        "device_status": device.status if device else None,
        "status": session.status,
        "created_at": session.created_at,
        "last_activity_at": session.last_activity_at,
        "expires_at": session.expires_at,
        "revoked_at": session.revoked_at,
    }


@router.get("/identities")
async def identities(
    search: str = Query("", max_length=100),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    access=Depends(require("platform.identities.read")),
    db: AsyncSession = Depends(get_session),
):
    filters = []
    if search:
        # Literal search, not user-controlled SQL LIKE wildcards.
        filters.append(
            or_(
                Identity.email.contains(search, autoescape=True),
                cast(Identity.id, String).contains(search, autoescape=True),
            )
        )
    total = await db.scalar(select(func.count()).select_from(Identity).where(*filters))
    rows = (
        await db.scalars(
            select(Identity)
            .where(*filters)
            .order_by(Identity.created_at.desc(), Identity.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {"total": total, "items": [identity_metadata(row) for row in rows]}


@router.get("/identities/{identity_id}")
async def identity_detail(
    identity_id: UUID,
    access=Depends(require("platform.identities.read")),
    db: AsyncSession = Depends(get_session),
):
    row = await db.get(Identity, identity_id)
    if row is None:
        raise DomainError("NOT_FOUND", "Account not found.", 404)
    return identity_metadata(row)


@router.get("/admins")
async def admins(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    access=Depends(require("platform.audit.read")),
    db: AsyncSession = Depends(get_session),
):
    rows = (
        await db.execute(
            select(PlatformGrant, Identity)
            .join(Identity, Identity.id == PlatformGrant.identity_id)
            .where(PlatformGrant.active.is_(True))
            .order_by(PlatformGrant.created_at.desc(), PlatformGrant.identity_id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {**identity_metadata(identity), "platform_role": grant.role} for grant, identity in rows
        ]
    }


@router.get("/sessions")
async def sessions(
    identity_id: UUID | None = None,
    status: SessionStatus | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    access=Depends(require("platform.sessions.read")),
    db: AsyncSession = Depends(get_session),
):
    if identity_id is not None and await db.get(Identity, identity_id) is None:
        raise DomainError("NOT_FOUND", "Account not found.", 404)
    filters = []
    if identity_id is not None:
        filters.append(Session.identity_id == identity_id)
    if status is not None:
        filters.append(Session.status == status)
    total = await db.scalar(select(func.count()).select_from(Session).where(*filters))
    rows = (
        await db.execute(
            select(Session, Device)
            .join(Device, Device.id == Session.device_id)
            .where(*filters)
            .order_by(Session.created_at.desc(), Session.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {
        "total": total,
        "items": [session_metadata(session, device) for session, device in rows],
    }


def record_platform_session_audit(
    db: AsyncSession, *, actor: UUID, role: str, action: str, target: UUID, result: str
) -> None:
    """Keep platform mutation records in the platform audit stream without credentials."""
    db.add(
        PlatformAudit(
            actor=f"{actor}:{role}",
            action=action,
            target=target,
            result=result,
        )
    )


@router.post("/sessions/{session_id}/revoke")
async def revoke_platform_session(
    session_id: UUID,
    request: Request,
    access=Depends(require("platform.sessions.revoke")),
    db: AsyncSession = Depends(get_session),
):
    """Idempotently revoke one session and its refresh-token family."""
    principal, grant, _ = access
    async with command_transaction(db):
        session = (
            await db.execute(select(Session).where(Session.id == session_id).with_for_update())
        ).scalar_one_or_none()
        if session is None:
            raise DomainError("SESSION_NOT_FOUND", "Session was not found.", 404)
        was_active = session.status == SessionStatus.ACTIVE
        await SessionService().revoke_session(
            db,
            session,
            request.state.correlation_id,
            request.client.host if request.client else "unknown",
            reason="PLATFORM_SESSION_REVOKED",
        )
        record_platform_session_audit(
            db,
            actor=principal.identity_id,
            role=grant.role,
            action="platform.session.revoke",
            target=session.id,
            result="REVOKED" if was_active else f"UNCHANGED:{session.status}",
        )
    return {"session_id": session.id, "status": session.status, "revoked": was_active}


@router.post("/identities/{identity_id}/sessions/revoke")
async def revoke_platform_identity_sessions(
    identity_id: UUID,
    request: Request,
    access=Depends(require("platform.sessions.revoke")),
    db: AsyncSession = Depends(get_session),
):
    """Revoke only active sessions belonging to the specified stable Identity ID."""
    principal, grant, _ = access
    async with command_transaction(db):
        if await db.get(Identity, identity_id) is None:
            raise DomainError("NOT_FOUND", "Account not found.", 404)
        active_sessions = (
            await db.scalars(
                select(Session)
                .where(Session.identity_id == identity_id, Session.status == SessionStatus.ACTIVE)
                .with_for_update()
            )
        ).all()
        for session in active_sessions:
            await SessionService().revoke_session(
                db,
                session,
                request.state.correlation_id,
                request.client.host if request.client else "unknown",
                reason="PLATFORM_USER_SESSIONS_REVOKED",
            )
        record_platform_session_audit(
            db,
            actor=principal.identity_id,
            role=grant.role,
            action="platform.user.sessions.revoke_all",
            target=identity_id,
            result=f"REVOKED:{len(active_sessions)}",
        )
    return {"identity_id": identity_id, "revoked_count": len(active_sessions)}


@router.get("/audit")
async def audit(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0, le=100000),
    access=Depends(require("platform.audit.read")),
    db: AsyncSession = Depends(get_session),
):
    rows = (
        await db.scalars(
            select(PlatformAudit)
            .order_by(PlatformAudit.created_at.desc(), PlatformAudit.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return {
        "items": [
            {
                "id": row.id,
                "actor": row.actor,
                "action": row.action,
                "target": row.target,
                "result": row.result,
                "created_at": row.created_at,
            }
            for row in rows
        ]
    }
