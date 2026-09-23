from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import Device, DeviceStatus, Session, SessionStatus
from app.schemas.api import DeviceResponse, RevokeResponse
from app.security.dependencies import Principal, current_principal
from app.services.audit import audit_and_event
from app.services.session_service import SessionService

router = APIRouter(prefix="/devices", tags=["devices"])


@router.get("", response_model=list[DeviceResponse])
async def devices(
    principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_session)
):
    rows = (
        (
            await db.execute(
                select(Device)
                .where(Device.identity_id == principal.identity_id)
                .order_by(Device.last_seen_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        DeviceResponse(
            id=row.id,
            platform=row.platform,
            device_name=row.device_name,
            device_model=row.device_model,
            status=row.status,
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            is_current=row.id == principal.device.id,
        )
        for row in rows
    ]


@router.get("/{device_id}", response_model=DeviceResponse)
async def device(
    device_id: UUID,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    row = (
        await db.execute(
            select(Device).where(
                Device.id == device_id, Device.identity_id == principal.identity_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise DomainError("DEVICE_NOT_FOUND", "Device was not found.", 404)
    return DeviceResponse(
        id=row.id,
        platform=row.platform,
        device_name=row.device_name,
        device_model=row.device_model,
        status=row.status,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
        is_current=row.id == principal.device.id,
    )


@router.post("/{device_id}/revoke", response_model=RevokeResponse)
async def revoke_device(
    device_id: UUID,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    """Revoking the current device is defined as logout of that device/session family."""
    async with db.begin():
        device = (
            await db.execute(
                select(Device)
                .where(Device.id == device_id, Device.identity_id == principal.identity_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if device is None:
            raise DomainError("DEVICE_NOT_FOUND", "Device was not found.", 404)
        now = datetime.now(UTC)
        device.status, device.revoked_at = DeviceStatus.REVOKED, now
        sessions = (
            (
                await db.execute(
                    select(Session)
                    .where(Session.device_id == device.id, Session.status == SessionStatus.ACTIVE)
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        service = SessionService()
        for row in sessions:
            await service.revoke_session(
                db,
                row,
                request.state.correlation_id,
                request.client.host if request.client else "unknown",
                "DEVICE_REVOKED",
            )
        await audit_and_event(
            db,
            action="DEVICE_REVOKED",
            event_type="device.revoked.v1",
            aggregate_type="device",
            aggregate_id=device.id,
            correlation_id=request.state.correlation_id,
            identity_id=principal.identity_id,
            device_id=device.id,
        )
    return RevokeResponse(status="REVOKED")
