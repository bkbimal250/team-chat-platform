# Gateway service

Public HTTPS ingress for GlobalChat JSON APIs. The gateway reverse-proxies `/api/v1/**` to the owning
microservice, forwards bearer JWTs and correlation headers, strips untrusted tenant/internal headers, and
applies edge rate limits plus security headers.

Realtime WebSocket traffic uses a **separate public host** (see `REALTIME_PUBLIC_WSS_URL`); this service
does not terminate WebSocket upgrades.

## Run locally

```bash
cd services/gateway-service
cp .env.example .env
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8008
```

Point web clients at `http://localhost:8008` and realtime at `ws://127.0.0.1:8007/api/v1/realtime`.

## Configuration

See `.env.example`. Production (`APP_ENV=production`) requires external upstream URLs, `REDIS_URL`, and
`REALTIME_PUBLIC_WSS_URL` with the `wss://` scheme. Rate limiting is enabled automatically in production.

## Operations

See [OPERATIONS.md](./OPERATIONS.md) for health checks, timeouts, limits, and reverse-proxy placement.

## Tests

```bash
uv run pytest
```
