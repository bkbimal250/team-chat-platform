# Conversation Service processes

Apply migrations before any process: `python -m alembic upgrade head`.

## API (HTTP)

`uvicorn app.main:app --host 0.0.0.0 --8003`

Production: set `APP_ENV=production` and configure `JWT_PUBLIC_KEY` plus `INTERNAL_SERVICE_TOKEN` (≥32 characters). See `.env.example`.

## Outbox publisher (required)

`python -m app.outbox_runner`

Publishes committed `outbox_events` rows to RabbitMQ exchange `organization.events` with routing keys matching `event_type`.

## Projection consumer (required)

`python -m app.consumer_runner`

Consumes organization membership events (`member.*`), user block events, and messaging summary events into local projections. Company `member.left` / `member.removed` events revoke workspace conversation membership; personal conversations are never modified.

## Configuration

`DATABASE_URL`, `REDIS_URL`, `RABBITMQ_URL`, `USER_SERVICE_URL`, and service auth token are required at runtime. Docker images default to the API process only; run outbox and consumer as separate containers or systemd units on VPS deployments.
