# Gateway operations

## Placement

- **Gateway**: public HTTPS (`api.michat.in` → gateway pods, port 8008).
- **Realtime**: public WSS (`ws.michat.in` → realtime pods, port 8007). Do not route WebSocket through the gateway.
- Upstream services are reached on internal DNS (`*.globalchat.internal`) configured via `*_URL` variables.

## Health

| Endpoint | Purpose |
|---|---|
| `GET /health/live` | Process liveness only. |
| `GET /health/ready` | Gateway initialized; does **not** probe downstreams (avoids restart loops on transient outages). |
| `GET /api/v1/platform/services` | Authenticated aggregate downstream live/ready; includes `realtime_public_wss_url`. |

## Limits and timeouts

| Setting | Default | Notes |
|---|---|---|
| `MAX_REQUEST_BYTES` | 2 MiB | JSON/metadata only; media bytes use presigned S3. |
| `UPSTREAM_CONNECT_TIMEOUT_SECONDS` | 3 | Per upstream connection. |
| `UPSTREAM_READ_TIMEOUT_SECONDS` | 15 | Per upstream response. |
| `UPSTREAM_IDEMPOTENT_RETRIES` | 1 | Extra attempt for `GET`/`HEAD` on connect/timeout errors only. |
| `RATE_LIMIT_AUTH_PER_MINUTE` | 20 | Per IP on auth/login/OTP/registration/password paths. |
| `RATE_LIMIT_API_PER_MINUTE` | 300 | Per IP on other `/api/v1/**` routes. |

Redis rate limiting fails **open** if Redis errors. Downstream `429` responses are forwarded unchanged.

## Security

- Allowlisted request headers; `Cookie`, `X-Organization-ID`, and `X-Internal-Token` are not forwarded.
- Response headers: `X-Content-Type-Options`, `Referrer-Policy`, `X-Frame-Options`, CSP `frame-ancestors`, `Permissions-Policy`; HSTS when `APP_ENV=production`.
- CORS allowlist via `CORS_ALLOWED_ORIGINS`.

## Errors

Gateway returns sanitized `502`/`504` JSON with `correlation_id`. Upstream status codes and bodies pass through for handled routes.
