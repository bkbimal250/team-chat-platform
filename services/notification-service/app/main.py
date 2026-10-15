from contextlib import asynccontextmanager
from uuid import UUID

from fastapi import Depends, FastAPI, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, engine, get_db_session
from app.models import Notification
from app.repositories import (
    ConversationMuteRepository,
    NotificationRepository,
    PreferenceRepository,
    PushTokenRepository,
    _tenant_filter,
)
from app.schemas import PreferencePatch, TokenRequest
from app.security import Principal, get_principal


@asynccontextmanager
async def lifespan(_app: FastAPI):
    get_settings()
    yield
    await engine.dispose()


app = FastAPI(title="Notification Service", version="1.0.0", lifespan=lifespan)


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}


@app.put("/api/v1/notifications/devices/current/token")
async def put_token(
    request: TokenRequest,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        return await PushTokenRepository(session).upsert_current_device(principal, request)


@app.delete("/api/v1/notifications/devices/current/token")
async def delete_token(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        await PushTokenRepository(session).disable_current_device(principal)
    return {"status": "disabled"}


@app.get("/api/v1/notifications/preferences")
async def get_preferences(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        return await PreferenceRepository(session).get_or_create(principal)


@app.patch("/api/v1/notifications/preferences")
async def patch_preferences(
    request: PreferencePatch,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        row = await PreferenceRepository(session).get_or_create(principal)
        if request.push_enabled is not None:
            row.push_enabled = request.push_enabled
        if request.notification_preview is not None:
            row.preview = request.notification_preview
        if request.message_notifications is not None:
            row.message_notifications = request.message_notifications
        if request.group_notifications is not None:
            row.group_notifications = request.group_notifications
        if request.sound_enabled is not None:
            row.sound_enabled = request.sound_enabled
        if request.vibration_enabled is not None:
            row.vibration_enabled = request.vibration_enabled
        return row


@app.put("/api/v1/notifications/conversations/{conversation_id}/mute")
async def mute_conversation(
    conversation_id: UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        await ConversationMuteRepository(session).mute(
            principal.organization_id,
            conversation_id,
            principal.user_id,
            principal.member_id,
        )
    return {"status": "muted"}


@app.delete("/api/v1/notifications/conversations/{conversation_id}/mute")
async def unmute_conversation(
    conversation_id: UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        await ConversationMuteRepository(session).unmute(
            principal.organization_id, conversation_id, principal.member_id
        )
    return {"status": "unmuted"}


@app.get("/api/v1/notifications")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    rows = (
        await session.scalars(
            select(Notification)
            .where(
                _tenant_filter(Notification.organization_id, principal.organization_id),
                Notification.recipient_member_id == principal.member_id,
                Notification.recipient_user_id == principal.user_id,
            )
            .order_by(Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": str(row.id),
            "conversation_id": str(row.conversation_id) if row.conversation_id else None,
            "message_id": str(row.message_id) if row.message_id else None,
            "notification_type": row.notification_type,
            "title": row.title,
            "body": row.body,
            "preview_mode": row.preview_mode,
            "read_at": row.read_at.isoformat() if row.read_at else None,
        }
        for row in rows
    ]


@app.get("/api/v1/notifications/unread-count")
async def unread_count(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        count = await NotificationRepository(session).unread_count(
            principal.organization_id, principal.member_id, principal.user_id
        )
    return {"unread_count": count}


@app.post("/api/v1/notifications/{notification_id}/read")
async def mark_read(
    notification_id: UUID,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        row = await NotificationRepository(session).mark_read(
            principal.organization_id,
            principal.member_id,
            principal.user_id,
            notification_id,
        )
    if row is None:
        return JSONResponse(status_code=404, content={"error": "notification not found"})
    return {"status": "read", "read_at": row.read_at.isoformat() if row.read_at else None}


@app.post("/api/v1/notifications/read-all")
async def mark_all_read(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        await NotificationRepository(session).mark_all_read(
            principal.organization_id, principal.member_id, principal.user_id
        )
    return {"status": "read"}
