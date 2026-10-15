# GlobalChat platform topology

## Public ingress

| Role | Production | Local |
|---|---|---|
| HTTPS JSON API | `https://api.michat.in` → **gateway-service** :8008 | `http://localhost:8008` |
| WebSocket realtime | `wss://ws.michat.in/api/v1/realtime` → **realtime-service** :8007 | `ws://127.0.0.1:8007/api/v1/realtime` |

Gateway reverse-proxies `/api/v1/**` to internal services. It does **not** terminate WebSocket upgrades.

## Application services (HTTP)

| Service | Port | Data |
|---|---:|---|
| organization-service | 8000 | Postgres |
| identity-service | 8001 | Postgres, Redis |
| user-service | 8002 | Postgres |
| conversation-service | 8003 | Postgres, Redis |
| messaging-service | 8004 | Postgres |
| media-service | 8005 | Postgres, S3 (prod) |
| notification-service | 8006 | Postgres |
| realtime-service | 8007 | Redis |
| gateway-service | 8008 | Redis (rate limits) |

## Async workers (per service)

See each service `docs/OPERATIONS.md` or `README.md`. Typical processes:

- **Outbox publishers** — organization, identity, user, conversation, messaging, media, notification
- **Rabbit consumers** — projections and fanout in messaging, conversation, user, identity, media, realtime, notification
- **Delivery / cleanup** — notification delivery worker, media cleanup runner, organization invitation expiry

## Shared infrastructure

| Component | Purpose |
|---|---|
| **PostgreSQL** | Authoritative per-service databases |
| **Redis** | OTP/rate limits, realtime presence, gateway rate limiting |
| **RabbitMQ** | Topic exchanges: `organization.events`, `user.events`, `messaging.events`, `media.events`, `notification.events` |
| **S3** | Media object bytes (presigned upload/download; not via gateway body) |

## Event routing summary

Documented in [EVENT_CONTRACT_MATRIX.md](./EVENT_CONTRACT_MATRIX.md). Most domain events publish to **`organization.events`** (including conversation and identity outbox), even when the producer is not the organization Django app.
