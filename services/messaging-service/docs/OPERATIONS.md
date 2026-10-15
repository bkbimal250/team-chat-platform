# Messaging Service processes

Run migrations first: `python -m alembic upgrade head`.

## API

`uvicorn app.main:app --host 0.0.0.0 --port 8004`

Set `APP_ENV=production`, `JWT_PUBLIC_KEY`, and `INTERNAL_SERVICE_TOKEN` (≥32 characters). See `.env.example`.

## Outbox publisher

`python -m app.outbox_runner`

Publishes `outbox_events` to exchange `messaging.events`.

## Authorization consumer

`python -m app.consumer_runner`

Projects conversation, organization member, media, and user block events. Required for workspace send authorization and org-member revocation.

Docker images default to the API process only; run publisher and consumer as separate processes on VPS/Kubernetes.
