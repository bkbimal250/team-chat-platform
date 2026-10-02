from contextlib import asynccontextmanager
from uuid import uuid4

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from app.config import Settings
from app.routing import owner_for

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


def create_app(
    settings: Settings | None = None, transport: httpx.AsyncBaseTransport | None = None
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
        try:
            yield
        finally:
            app.state.ready = False
            await app.state.upstreams.aclose()

    app = FastAPI(title="GlobalChat API Gateway", version="1.0.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=sorted(REQUEST_HEADERS),
    )

    @app.get("/health/live", include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        initialized = bool(getattr(request.app.state, "ready", False))
        return JSONResponse(
            {"status": "ready" if initialized else "not_ready"},
            status_code=200 if initialized else 503,
        )

    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
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
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
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
