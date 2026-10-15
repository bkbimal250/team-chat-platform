# Realtime WebSocket

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Use Postman WebSocket ws://localhost:8007/api/v1/realtime?token=<private-access-token>. Send version1 ping, subscribe conversation_id, typing.start/typing.stop and presence.heartbeat. Subscribe two authorized users; send HTTP message, observe recipient frames. Invalid authorization closes1008, shutdown1012; reconnect/resubscribe. Never export query tokens.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [realtime](../services/REALTIME-API.md) | None at this layer |
| GET | `/health/ready` | [realtime](../services/REALTIME-API.md) | None at this layer |
| WEBSOCKET | `/api/v1/realtime` | [realtime](../services/REALTIME-API.md) | Access token in query; conversation authorization |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
