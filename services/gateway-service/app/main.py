import asyncio
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from redis.asyncio import Redis

from app.config import Settings
from app.rate_limit import (
    MemoryRateLimitStore,
    RedisRateLimitStore,
    check_rate_limits,
)
from app.routing import normalize_path, owner_for
from app.security_headers import SecurityHeadersMiddleware

REQUEST_HEADERS = {
    "accept",
    "accept-language",
    "authorization",
    "content-type",
    "idempotency-key",
    "user-agent",
    "x-correlation-id",
    "x-request-id",
}
RESPONSE_HEADERS = {
    "cache-control",
    "content-disposition",
    "content-language",
    "content-type",
    "etag",
    "location",
    "retry-after",
    "x-correlation-id",
    "x-request-id",
}


def _safe_correlation_id(value: str | None) -> str:
    if value and len(value) <= 128 and all(ch.isalnum() or ch in "-_." for ch in value):
        return value
    return str(uuid4())


async def _upstream_request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    params,
    headers: dict[str, str],
    content: bytes,
    retries: int,
) -> httpx.Response:
    attempts = retries + 1 if method in {"GET", "HEAD"} else 1
    last_error: Exception | None = None
    for attempt in range(attempts):
        try:
            return await client.request(
                method, url, params=params, headers=headers, content=content
            )
        except (httpx.TimeoutException, httpx.RequestError) as exc:
            last_error = exc
            if attempt + 1 < attempts:
                await asyncio.sleep(0.05 * (attempt + 1))
                continue
            raise last_error
    raise RuntimeError("unreachable")


def create_app(
    settings: Settings | None = None,
    transport: httpx.AsyncBaseTransport | None = None,
    rate_limit_store=None,
) -> FastAPI:
    config = settings or Settings()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        timeout = httpx.Timeout(
            connect=config.upstream_connect_timeout_seconds,
            read=config.upstream_read_timeout_seconds,
            write=config.upstream_read_timeout_seconds,
            pool=config.upstream_connect_timeout_seconds,
        )
        app.state.upstreams = httpx.AsyncClient(
            timeout=timeout,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
            transport=transport,
            follow_redirects=False,
        )
        app.state.ready = True
        app.state.config = config
        app.state.redis = None
        app.state.rate_limit_store = rate_limit_store
        if app.state.rate_limit_store is None and config.rate_limit_enabled and config.redis_url:
            app.state.redis = Redis.from_url(config.redis_url, decode_responses=False)
            app.state.rate_limit_store = RedisRateLimitStore(app.state.redis)
        elif app.state.rate_limit_store is None and config.rate_limit_enabled:
            app.state.rate_limit_store = MemoryRateLimitStore()
        try:
            yield
        finally:
            app.state.ready = False
            await app.state.upstreams.aclose()
            if app.state.redis is not None:
                await app.state.redis.aclose()

    app = FastAPI(title="GlobalChat API Gateway", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=sorted(REQUEST_HEADERS),
    )
    app.add_middleware(SecurityHeadersMiddleware, production=config.app_env == "production")

    @app.middleware("http")
    async def gateway_rate_limit(request: Request, call_next):
        store = getattr(request.app.state, "rate_limit_store", None)
        try:
            blocked = await check_rate_limits(
                request,
                store,
                enabled=config.rate_limit_enabled,
                auth_limit=config.rate_limit_auth_per_minute,
                auth_window=config.rate_limit_window_seconds,
                api_limit=config.rate_limit_api_per_minute,
                api_window=config.rate_limit_window_seconds,
            )
        except Exception:
            blocked = None
        if blocked is not None:
            return blocked
        return await call_next(request)

    @app.get("/health/live", include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        initialized = bool(getattr(request.app.state, "ready", False))
        payload = {
            "status": "ready" if initialized else "not_ready",
            "rate_limit_enabled": config.rate_limit_enabled,
        }
        return JSONResponse(payload, status_code=200 if initialized else 503)

    @app.get("/api/v1/platform/services")
    async def service_status(request: Request):
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            return JSONResponse({"detail": "Authentication required"}, status_code=401)
        try:
            result = await request.app.state.upstreams.get(
                config.upstreams["identity"] + "/api/v1/platform/me",
                headers={"authorization": authorization},
            )
            if result.status_code in {401, 403, 429}:
                return JSONResponse(
                    {"detail": "Platform authorization required"},
                    status_code=result.status_code,
                )
            if result.status_code != 200 or "platform.services.read" not in result.json().get(
                "permissions", []
            ):
                return JSONResponse(
                    {"detail": "Platform authorization unavailable"}, status_code=503
                )
        except (httpx.HTTPError, ValueError):
            return JSONResponse({"detail": "Platform authorization unavailable"}, status_code=503)

        async def check(name, base):
            async def probe(path):
                try:
                    response = await request.app.state.upstreams.get(base + path, timeout=3)
                    return response.status_code == 200
                except httpx.HTTPError:
                    return False

            live, ready = await asyncio.gather(probe("/health/live"), probe("/health/ready"))
            return {"name": name, "live": live, "ready": ready}

        rows = await asyncio.gather(*(check(name, base) for name, base in config.upstreams.items()))
        rows.append(
            {
                "name": "gateway",
                "live": True,
                "ready": bool(getattr(request.app.state, "ready", False)),
            }
        )
        return {
            "checked_at": datetime.now(UTC).isoformat(),
            "realtime_public_wss_url": config.realtime_public_wss_url,
            "items": rows,
        }

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = normalize_path(f"/{path}")
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        # Normalize for route ownership, but preserve the downstream URL contract.
        upstream_path = public_path + ("/" if path.endswith("/") and public_path != "/" else "")
        url = f"{config.upstreams[owner]}{upstream_path}"
        try:
            upstream = await _upstream_request(
                request.app.state.upstreams,
                request.method,
                url,
                params=request.query_params,
                headers=headers,
                content=body,
                retries=config.upstream_idempotent_retries,
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )

    return app


app = create_app()
