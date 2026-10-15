# Realtime Service

WebSocket gateway for live message, typing, and presence updates. Consumes Messaging and Organization events through a separate consumer process and routes deliveries through Redis when horizontally scaled.

## Scopes

- **Personal:** JWT without `org`; subscriptions authorize through Conversation Service.
- **Workspace:** JWT with `org` + `mid`; org `member.left/removed` revokes all workspace subscriptions without affecting personal sockets.

Missed messages are **not** stored here. Clients reconnect, resubscribe, and backfill from Messaging history. Queue overflow emits `connection.resync_required.v1`.

## Processes

See [docs/OPERATIONS.md](docs/OPERATIONS.md).
