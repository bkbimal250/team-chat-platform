# Realtime

```
Mobile → REALTIME_WSS_URL?token=<access_token>
```

Implementation: `lib/services/realtime/realtime_client.dart`

## Connect

- URL from `AppConfig.realtimeWssUrl` (override with `--dart-define=REALTIME_WSS_URL=...`).
- Pass the current bearer access token as query param `token` (never log the URL or token).
- On `connection.ready.v1`, resubscribe all conversation ids the client still cares about.

## Client → server (version 1)

| type | Purpose |
|------|---------|
| `ping` | Keepalive → `pong` |
| `subscribe` / `unsubscribe` | `conversation_id` |
| `typing.start` / `typing.stop` | Requires active subscription |
| `e2ee.sender_key_distribution` | Fan-out sender-key ciphertext to other subscribers (no plaintext) |

## Server → client

| type | Action |
|------|--------|
| `message.created.v1` (and related) | Refresh messaging history for that conversation |
| `connection.resync_required.v1` | Re-fetch history from Messaging API |
| `e2ee.sender_key_distribution.v1` | Process distribution into local sender-key store |
| `typing.updated.v1` | UI typing indicators |

Missed messages are **not** stored on the realtime service. After reconnect, subscribe again and backfill via `GET /api/v1/conversations/{id}/messages`.
