# Realtime Service processes

## API (WebSocket + health)

`uvicorn app.main:app --host 0.0.0.0 --port 8007`

Requires `REDIS_URL` in production for shared routing metadata and presence TTL.

## Event consumer (required)

`python -m app.consumer_runner`

Requires `REDIS_URL` and `RABBITMQ_URL` (non-localhost when `APP_ENV=production`). Binds `messaging.events` (`message.#`) and `organization.events` (`conversation.#`, `member.#`).

Production also requires `JWT_PUBLIC_KEY`, `INTERNAL_SERVICE_TOKEN` (≥32 chars), and `CONVERSATION_SERVICE_URL`. Optional `USER_SERVICE_URL` for personal presence privacy checks.
