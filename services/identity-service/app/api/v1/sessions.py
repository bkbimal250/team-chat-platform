from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import Device, Session
from app.schemas.api import RevokeResponse, SessionResponse
from app.security.dependencies import Principal, current_principal
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth/sessions", tags=["sessions"])


@router.get("", response_model=list[SessionResponse])
async def sessions(
    principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_session)
):
    rows = (
        await db.execute(
            select(Session, Device)
            .join(Device, Device.id == Session.device_id)
            .where(Session.identity_id == principal.identity_id)
            .order_by(Session.last_activity_at.desc())
        )
    ).all()
    return [
        SessionResponse(
            id=session.id,
            device_id=device.id,
            platform=device.platform,
            device_name=device.device_name,
            status=session.status,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            is_current=session.id == principal.session.id,
        )
        for session, device in rows
    ]


@router.post("/{session_id}/revoke", response_model=RevokeResponse)
async def revoke(
    session_id: UUID,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        session = (
            await db.execute(
                select(Session)
                .where(Session.id == session_id, Session.identity_id == principal.identity_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if session is None:
            raise DomainError("SESSION_NOT_FOUND", "Session was not found.", 404)
        await SessionService().revoke_session(
            db,
            session,
            request.state.correlation_id,
            request.client.host if request.client else "unknown",
        )
    return RevokeResponse(status="REVOKED")
