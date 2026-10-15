# Identity service operations

## API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

Production requires external PostgreSQL, `REDIS_URL`, `RABBITMQ_URL`, and `JWT_*` signing configuration.

## Outbox publisher

Publishes identity and auth security events to exchange **`organization.events`** (routing keys `identity.*`, `auth.*`, `device.*`, `session.*`).

Run the identity outbox worker documented in the service README / local `scripts/local/dev.py` profile.

## Rabbit consumer

Queue **`identity.membership`** on **`organization.events`**:

- `member.#` — membership projections (`member.*.v2` authoritative)
- `organization.#` — organization suspension, etc.

ACK only after the consumer transaction commits.

## Health

- `GET /health/live` — process liveness
- `GET /health/ready` — database and Redis readiness (see service implementation)

## Personal vs workspace sessions

Login and token issue accept optional `organization_id`. Null organization yields a **personal** session (`organization_id` / `member_id` absent in JWT). Workspace login requires an active membership from organization-service.
