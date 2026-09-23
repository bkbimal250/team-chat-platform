from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from redis.asyncio import Redis
from sqlalchemy import text

from app.api import internal_router, router
from app.core import DomainError, error_handler, logging_setup, request_context, settings
from app.db import Sessions, engine


@asynccontextmanager
async def life(app):
    logging_setup()
    app.state.redis = Redis.from_url(str(settings().redis_url), decode_responses=True)
    yield
    await app.state.redis.aclose()
    await engine.dispose()


app = FastAPI(
    title="Conversation Service",
    version="1.0.0",
    docs_url="/api/docs" if settings().app_env != "production" else None,
    openapi_url="/api/schema/" if settings().app_env != "production" else None,
    lifespan=life,
)
app.add_exception_handler(DomainError, error_handler)
app.middleware("http")(request_context)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=[
        "Content-Type",
        "Authorization",
        "X-Correlation-ID",
        "X-Internal-Service-Token",
        "X-Organization-ID",
        "X-Member-ID",
    ],
)


@app.get("/health/live")
async def live():
    return {"status": "alive"}


@app.get("/health/ready")
async def ready(request: Request):
    try:
        async with Sessions() as s:
            await s.execute(text("SELECT 1"))
        await request.app.state.redis.ping()
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {
        "status": "ready",
        "database": "available",
        "redis": "available",
        "broker": "asynchronous",
    }


app.include_router(router)
app.include_router(internal_router)
