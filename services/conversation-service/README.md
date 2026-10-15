# Conversation Service

Owns conversation structure for GlobalChat: personal and workspace (company) scopes, direct and group types, membership roles, per-member list state, group settings, chat summary projections, and transactional outbox events. It does not store message bodies (Messaging Service) or deliver notifications.

## Scopes

| Scope | `organization_id` | JWT context | Types |
| --- | --- | --- | --- |
| Personal | `null` | Bearer with `sub` only | `POST /personal/direct`, `POST /personal/groups` |
| Workspace | company UUID | Bearer with `org` + `mid` | `POST /direct`, `POST /groups` |

`member_id` in workspace APIs is the organization member UUID. Personal APIs use identity UUIDs as `member_id` and resolve contacts through User Service (`/internal/v1/contacts/authorize`).

Team and branch entities are not conversations; workspace chats are company-scoped groups or direct messages between members.

## Membership and org lifecycle

Workspace access requires an active `ConversationMember` row and an active `member_projections` row for the organization (defense in depth on list, get, and internal authorize). Organization `member.left.v2` / `member.removed.v2` events bulk-revoke all workspace conversation memberships for that member. `member.reactivated.v2` updates the projection only; conversation memberships are not restored automatically. Personal direct chats and personal groups are never changed by organization events.

## Local development

```powershell
python -m uv sync --python 3.12
python -m alembic upgrade head
python -m uv run uvicorn app.main:app --port 8003
python -m uv run pytest -q
```

Swagger: `http://localhost:8003/api/docs/` (non-production). Health: `/health/live`, `/health/ready` (PostgreSQL + Redis).

## Production processes

See [docs/OPERATIONS.md](docs/OPERATIONS.md) for API, outbox publisher, and consumer commands.

Direct chats use a sorted `direct_key` with uniqueness per scope. Groups support OWNER / ADMIN / MEMBER, ownership transfer, close (`conversation.closed.v1`), and owner delete (`conversation.deleted.v1`). `ConversationSettings` gate member invites and metadata edits.
