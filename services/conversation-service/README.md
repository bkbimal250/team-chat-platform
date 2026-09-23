# Conversation Service

Phase 4 owns only conversation structure: direct/group conversations, membership, roles, per-member list state, group settings, and domain outbox rows. It intentionally has no messages, delivery, WebSockets, media, or notifications.

`member_id` is the authoritative tenant membership reference. `user_id` is deliberately nullable projection data and is never invented.

## Important integration boundary

The required Phase 3 `user-service` is absent in this workspace. This service therefore includes no fallback block-check or profile lookup: production integration must fail closed through an explicit `UserServiceClient` before direct conversation creation is enabled at the gateway. Likewise, the current request-context adapter expects a gateway-verified internal service token plus immutable `X-Organization-ID`/`X-Member-ID` headers. It is a deployment boundary, not public authentication; production must terminate user JWT validation at a trusted gateway or replace this adapter with direct verified identity JWT validation.

Run after supplying the variables from `.env.example`:

```powershell
python -m uv sync --python 3.12
python -m uv run alembic upgrade head
python -m uv run uvicorn app.main:app --port 8003
```

Swagger is at `http://localhost:8003/api/docs/`; health is `/health/live` and `/health/ready`.

Direct conversations use a sorted UUID `direct_key` with a unique `(organization_id, direct_key)` constraint. Groups have one OWNER at creation; ownership transfer changes old OWNER to ADMIN and new member to OWNER in one transaction. Owners must transfer before leaving. Personal archive, pin and mute state lives in `conversation_member_states`.
