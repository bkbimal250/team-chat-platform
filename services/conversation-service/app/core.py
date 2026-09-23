import json
import logging
import re
import time
from datetime import UTC, datetime
from functools import lru_cache
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import Field, PostgresDsn, RedisDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "local"
    service_name: str = "conversation-service"
    database_url: PostgresDsn
    redis_url: RedisDsn
    rabbitmq_url: str
    identity_service_url: str
    organization_service_url: str
    user_service_url: str
    internal_service_token: str = Field(min_length=32)
    default_group_member_limit: int = Field(default=250, ge=2, le=10000)
    cors_allowed_origins: str = ""
    database_pool_size: int = 10
    database_max_overflow: int = 10

    @property
    def cors_origins(self):
        return [x for x in self.cors_allowed_origins.split(",") if x]


@lru_cache
def settings():
    return Settings()


class DomainError(Exception):
    def __init__(self, code, message, status=409, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details or {}


async def error_handler(request: Request, exc: DomainError):
    return JSONResponse(
        status_code=exc.status,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "correlation_id": request.state.correlation_id,
            }
        },
    )


class Formatter(logging.Formatter):
    def format(self, r):
        base = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": r.levelname,
            "service": settings().service_name,
            "environment": settings().app_env,
            "message": r.getMessage(),
        }
        for key in (
            "correlation_id",
            "member_id",
            "organization_id",
            "conversation_id",
            "status",
            "duration_ms",
        ):
            if hasattr(r, key):
                base[key] = str(getattr(r, key))
        return json.dumps(base)


def logging_setup():
    h = logging.StreamHandler()
    h.setFormatter(Formatter())
    logging.basicConfig(level="INFO", handlers=[h], force=True)


async def request_context(request, call_next):
    c = request.headers.get("X-Correlation-ID", "")
    request.state.correlation_id = c if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", c) else str(uuid4())
    start = time.monotonic()
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = request.state.correlation_id
    logging.getLogger("requests").info(
        "http_request",
        extra={
            "correlation_id": request.state.correlation_id,
            "status": response.status_code,
            "duration_ms": round((time.monotonic() - start) * 1000, 2),
        },
    )
    return response
