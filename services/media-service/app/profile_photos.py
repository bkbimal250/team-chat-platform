"""Account-owned private images; visibility is authorized by User Service."""
import hmac
from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import func, select

from app.config import get_settings
from app.db import SessionLocal
from app.models import ProfilePhoto
from app.security import Principal, get_principal
from app.storage import StorageError

router = APIRouter()
class Upload(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mime_type: Literal["image/jpeg", "image/png", "image/webp"]
    size_bytes: int = Field(gt=0, le=2 * 1024 * 1024)

async def internal(x_internal_service_token: str | None = Header(default=None)):
    expected = get_settings().internal_service_token
    if not expected or not x_internal_service_token or not hmac.compare_digest(expected, x_internal_service_token):
        raise HTTPException(403, "Internal authorization required")

@router.post("/api/v1/media/profile-photos/uploads", status_code=201)
async def upload(body: Upload, request: Request, principal: Principal = Depends(get_principal)):
    service = request.app.state.media_service
    async with SessionLocal.begin() as db:
        # Bound pending/upload churn per authenticated account, not per tenant.
        await db.execute(select(func.pg_advisory_xact_lock(func.hashtextextended(str(principal.user_id), 0))))
        count = await db.scalar(select(func.count()).select_from(ProfilePhoto).where(
            ProfilePhoto.owner_identity_id == principal.user_id,
            ProfilePhoto.created_at > datetime.now(UTC) - timedelta(hours=1)))
        if count >= 10:
            raise HTTPException(429, "Too many photo uploads. Try again later.")
        photo = ProfilePhoto(id=uuid4(), owner_identity_id=principal.user_id,
            object_key=f"profile-photos/{principal.user_id}/{uuid4()}",
            mime_type=body.mime_type, size_bytes=body.size_bytes, ready=False)
        db.add(photo)
        try:
            url, headers, expiry = await service.storage.presign_upload(service.policy.bucket,
                photo.object_key, photo.mime_type, datetime.now(UTC) + timedelta(minutes=5))
        except StorageError:
            raise HTTPException(503, "Photo storage unavailable") from None
    return {"media_id": str(photo.id), "upload_url": url, "required_headers": headers, "expires_at": expiry}

@router.post("/api/v1/media/profile-photos/{photo_id}/complete")
async def complete(photo_id: UUID, request: Request, principal: Principal = Depends(get_principal)):
    service = request.app.state.media_service
    async with SessionLocal.begin() as db:
        photo = await db.get(ProfilePhoto, photo_id)
        if photo is None or photo.owner_identity_id != principal.user_id:
            raise HTTPException(404, "Photo unavailable")
        try:
            info = await service.storage.head(service.policy.bucket, photo.object_key)
        except StorageError:
            raise HTTPException(503, "Photo storage unavailable") from None
        if not info or info.size_bytes != photo.size_bytes or info.mime_type != photo.mime_type:
            raise HTTPException(409, "Uploaded photo does not match its metadata")
        photo.ready = True
    return {"media_id": str(photo.id), "ready": True}

class Resolve(BaseModel):
    owner_identity_id: UUID
    ttl: int = Field(default=30, ge=1, le=60)

@router.post("/internal/v1/media/profile-photos/{photo_id}", dependencies=[Depends(internal)])
async def resolve(photo_id: UUID, body: Resolve, request: Request):
    service = request.app.state.media_service
    async with SessionLocal() as db:
        photo = await db.get(ProfilePhoto, photo_id)
        if not photo or photo.owner_identity_id != body.owner_identity_id or not photo.ready:
            raise HTTPException(404, "Photo unavailable")
        try:
            url = await service.storage.presign_download(service.policy.bucket, photo.object_key, body.ttl)
        except StorageError:
            raise HTTPException(503, "Photo storage unavailable") from None
    return {"download_url": url}
