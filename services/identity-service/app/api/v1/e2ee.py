from uuid import UUID

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import client_ip
from app.core.errors import DomainError
from app.db.session import command_transaction, get_session
from app.models.models import Device
from app.schemas.e2ee import (
    DeviceKeysUpload,
    PreKeyBundleResponse,
    PreKeyReplenishRequest,
    PublicDeviceE2eeResponse,
)
from app.security.dependencies import Principal, current_principal
from app.services.e2ee_service import E2eeService
from app.services.rate_limit import RateLimiter

router = APIRouter(tags=["e2ee"])
devices_e2ee = APIRouter(prefix="/devices", tags=["e2ee"])
users_e2ee = APIRouter(prefix="/users", tags=["e2ee"])
e2ee_router = APIRouter(prefix="/e2ee", tags=["e2ee"])


async def _own_device(
    device_id: UUID, principal: Principal, db: AsyncSession
) -> Device:
    if device_id != principal.device.id:
        raise DomainError("DEVICE_FORBIDDEN", "You may only modify this device.", 403)
    return principal.device


@devices_e2ee.put("/{device_id}/keys", status_code=204, response_class=Response)
async def upload_device_keys(
    device_id: UUID,
    payload: DeviceKeysUpload,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"e2ee:upload:{principal.identity_id}", 30, 3600
    )
    device = await _own_device(device_id, principal, db)
    async with command_transaction(db):
        await E2eeService().upsert_device_keys(db, device, payload)
    return Response(status_code=204)


@devices_e2ee.post("/{device_id}/prekeys/replenish")
async def replenish_prekeys(
    device_id: UUID,
    payload: PreKeyReplenishRequest,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"e2ee:replenish:{principal.identity_id}", 60, 3600
    )
    device = await _own_device(device_id, principal, db)
    async with command_transaction(db):
        added = await E2eeService().replenish(db, device, payload)
    return {"added": added}


@users_e2ee.get("/{identity_id}/devices", response_model=list[PublicDeviceE2eeResponse])
async def list_user_devices(
    identity_id: UUID,
    request: Request,
    _: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"e2ee:list-devices:{client_ip(request)}", 120, 3600
    )
    rows = await E2eeService().list_identity_devices(db, identity_id)
    return [PublicDeviceE2eeResponse(**row) for row in rows]


@e2ee_router.get(
    "/prekey-bundle/{identity_id}/{device_id}",
    response_model=PreKeyBundleResponse,
)
async def prekey_bundle(
    identity_id: UUID,
    device_id: UUID,
    request: Request,
    _: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"e2ee:bundle:{client_ip(request)}", 240, 3600
    )
    async with command_transaction(db):
        bundle = await E2eeService().fetch_prekey_bundle(db, identity_id, device_id)
    return PreKeyBundleResponse(**bundle)
