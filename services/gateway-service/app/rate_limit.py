import re
from typing import Protocol

from fastapi import Request
from fastapi.responses import JSONResponse

from app.routing import normalize_path

SENSITIVE_AUTH_PREFIXES = (
    "/api/v1/auth/login",
    "/api/v1/auth/otp",
    "/api/v1/auth/registration",
    "/api/v1/auth/password",
    "/api/v1/auth/invitations",
    "/api/v1/auth/qr",
    "/api/v1/auth/refresh",
    "/api/v1/auth/logout",
)

SKIP_PREFIXES = ("/health/live", "/health/ready")


class RateLimitStore(Protocol):
    async def consume(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        """Return (allowed, retry_after_seconds)."""


class RedisRateLimitStore:
    def __init__(self, redis) -> None:
        self._redis = redis

    async def consume(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        value = await self._redis.incr(key)
        if value == 1:
            await self._redis.expire(key, window_seconds)
        ttl = await self._redis.ttl(key)
        retry_after = max(1, ttl if isinstance(ttl, int) and ttl > 0 else window_seconds)
        return value <= limit, retry_after


class MemoryRateLimitStore:
    """Test/local fallback when Redis is unavailable."""

    def __init__(self) -> None:
        self._counts: dict[str, int] = {}

    async def consume(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        self._counts[key] = self._counts.get(key, 0) + 1
        return self._counts[key] <= limit, window_seconds


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    if forwarded:
        candidate = forwarded.split(",")[0].strip()
        if candidate:
            return candidate
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def is_sensitive_auth_path(path: str) -> bool:
    normalized = normalize_path(path)
    return any(normalized.startswith(prefix) for prefix in SENSITIVE_AUTH_PREFIXES)


def should_skip_rate_limit(path: str) -> bool:
    normalized = normalize_path(path)
    return normalized in SKIP_PREFIXES


def rate_limit_key(kind: str, ip: str, path: str) -> str:
    safe_path = re.sub(r"[^a-zA-Z0-9/_-]", "_", path)[:120]
    return f"gateway:rl:{kind}:{ip}:{safe_path}"


async def check_rate_limits(
    request: Request,
    store: RateLimitStore | None,
    *,
    enabled: bool,
    auth_limit: int,
    auth_window: int,
    api_limit: int,
    api_window: int,
) -> JSONResponse | None:
    if not enabled or store is None or should_skip_rate_limit(request.url.path):
        return None

    path = normalize_path(request.url.path)
    if not path.startswith("/api/v1/"):
        return None

    ip = client_ip(request)
    if is_sensitive_auth_path(path):
        allowed, retry_after = await store.consume(
            rate_limit_key("auth", ip, path), auth_limit, auth_window
        )
        if not allowed:
            return JSONResponse(
                {"detail": "Too many requests", "retry_after": retry_after},
                status_code=429,
                headers={"Retry-After": str(retry_after)},
            )
        return None

    allowed, retry_after = await store.consume(
        rate_limit_key("api", ip, "public"), api_limit, api_window
    )
    if not allowed:
        return JSONResponse(
            {"detail": "Too many requests", "retry_after": retry_after},
            status_code=429,
            headers={"Retry-After": str(retry_after)},
        )
    return None
