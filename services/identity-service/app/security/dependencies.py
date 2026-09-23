from dataclasses import dataclass
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import Device, Session, SessionStatus
from app.security.tokens import decode_access_token

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    identity_id: UUID
    session: Session
    device: Device


async def current_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    db: AsyncSession = Depends(get_session),
) -> Principal:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise DomainError("NOT_AUTHENTICATED", "Authentication is required.", 401)
    claims = decode_access_token(credentials.credentials)
    try:
        session_id, identity_id, device_id = (
            UUID(claims["sid"]),
            UUID(claims["sub"]),
            UUID(claims["did"]),
        )
    except (ValueError, KeyError) as exc:
        raise DomainError("ACCESS_TOKEN_INVALID", "Authentication is required.", 401) from exc
    session = (
        await db.execute(
            select(Session)
            .where(Session.id == session_id, Session.identity_id == identity_id)
            .with_for_update()
        )
    ).scalar_one_or_none()
    if session is None or session.status != SessionStatus.ACTIVE:
        raise DomainError("SESSION_REVOKED", "This session is no longer active.", 401)
    device = (
        await db.execute(
            select(Device).where(Device.id == device_id, Device.identity_id == identity_id)
        )
    ).scalar_one_or_none()
    if device is None or device.status != "ACTIVE":
        raise DomainError("DEVICE_REVOKED", "This device is no longer active.", 401)
    request.state.identity_id, request.state.session_id, request.state.device_id = (
        identity_id,
        session.id,
        device.id,
    )
    request.state.organization_id, request.state.member_id = (
        session.organization_id,
        session.member_id,
    )
    return Principal(identity_id, session, device)
