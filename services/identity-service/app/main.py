import logging
import re
import time
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.api.v1 import auth, devices, sessions
from app.core.config import get_settings
from app.core.errors import DomainError, domain_error_handler
from app.core.logging import configure_logging
from app.db.session import SessionLocal, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings)
    app.state.redis = Redis.from_url(
        str(settings.redis_url),
        max_connections=settings.redis_max_connections,
        decode_responses=True,
    )
    yield
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="Identity Service",
    version="1.0.0",
    description="Phase 2 platform authentication. All business membership authorization is delegated to Organization Service.",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url="/api/redoc" if settings.app_env != "production" else None,
    openapi_url="/api/schema/" if settings.app_env != "production" else None,
    lifespan=lifespan,
)
app.add_exception_handler(DomainError, domain_error_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Authorization", "Content-Type", "X-Correlation-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    supplied = request.headers.get("X-Correlation-ID", "")
    request.state.correlation_id = (
        supplied if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied) else str(uuid4())
    )
    started = time.monotonic()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    logging.getLogger("requests").info(
        "http_request",
        extra={
            "correlation_id": request.state.correlation_id,
            "path": request.url.path,
            "method": request.method,
            "status": response.status_code,
            "duration_ms": round((time.monotonic() - started) * 1000, 2),
            **{
                field: getattr(request.state, field, None)
                for field in (
                    "identity_id",
                    "organization_id",
                    "member_id",
                    "session_id",
                    "device_id",
                )
            },
        },
    )
    return response


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed.",
                "details": exc.errors(),
                "correlation_id": request.state.correlation_id,
            }
        },
    )


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready(request: Request):
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        await request.app.state.redis.ping()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {
        "status": "ready",
        "database": "available",
        "redis": "available",
        "broker": "asynchronous; monitored by outbox worker",
    }


app.include_router(auth.router, prefix="/api/v1")
app.include_router(devices.router, prefix="/api/v1")
app.include_router(sessions.router, prefix="/api/v1")
