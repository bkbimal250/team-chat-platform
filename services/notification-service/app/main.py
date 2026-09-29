from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db import SessionLocal, engine, get_db_session
from app.repositories import PreferenceRepository, PushTokenRepository
from app.schemas import PreferencePatch, TokenRequest
from app.security import Principal, get_principal


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Validate production authentication/provider configuration before serving traffic.
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
        return row
