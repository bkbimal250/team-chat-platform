# Media Service operations

## API

`uvicorn app.main:app --host 0.0.0.0 --port 8005`

Production requires `MEDIA_STORAGE_BACKEND=s3`, external PostgreSQL, `JWT_PUBLIC_KEY`, `INTERNAL_SERVICE_TOKEN`, and `CONVERSATION_API_URL`.

## Reference consumer

`python -m app.consumer_runner`

Requires `RABBITMQ_URL` and `DATABASE_URL` (durable mode). Consumes `messaging.events` (`message.created/deleted.v1`) and `organization.events` (`member.left/removed/reactivated.v2`).

## Outbox publisher

`python -m app.outbox_runner`

Publishes pending `media.*` events to `media.events`.

## Cleanup job

`python -m app.cleanup_runner`

Runs orphan PENDING/multipart cleanup and GC for unreferenced `READY` media past retention (`MEDIA_CLEANUP_INTERVAL_SECONDS`, default 3600).
