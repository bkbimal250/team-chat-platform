# Messaging Service

Stores messages, reactions, read/delivery state, and personal broadcast lists. Publishes `message.*` events to RabbitMQ `messaging.events` for Realtime/Notification consumers. Authorizes sends through local conversation projections plus Conversation Service internal authorize for personal scope.

## Scopes

- **Workspace:** JWT with `org` + `mid`; messages keyed by `organization_id`.
- **Personal:** JWT with `sub` only; `organization_id` null; Conversation Service is authoritative for membership and personal block/privacy rules.

Organization `member.left/removed` events update `organization_member_projections` and deny workspace operations even if stale conversation rows exist. Conversation `member_left/removed` events honor `resulting_status`. Personal data is never updated by organization events.

## Personal broadcast lists

Broadcast lists are not group conversations. `POST /api/v1/personal/broadcast-lists/{id}/messages` fans out independent messages (one per recipient direct chat) and emits one `message.created.v1` per delivery. Company/workspace broadcast is not implemented.

## Local development

```powershell
python -m uv sync --python 3.12
python -m alembic upgrade head
python -m uv run uvicorn app.main:app --port 8004
python -m uv run pytest -q
```

## Production processes

See [docs/OPERATIONS.md](docs/OPERATIONS.md).
