# Notifications

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

GET inbox with limit/offset and preferences. PATCH only supported push_enabled/notification_preview. Push-token API binds current device JWT. Do not register fake provider tokens or send real FCM. Mark-read/unread/mark-all-read/browser-push unavailable; no invented requests.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [notification](../services/NOTIFICATION-API.md) | None at this layer |
| GET | `/health/ready` | [notification](../services/NOTIFICATION-API.md) | None at this layer |
| PUT | `/api/v1/notifications/devices/current/token` | [notification](../services/NOTIFICATION-API.md) | Bearer access token |
| DELETE | `/api/v1/notifications/devices/current/token` | [notification](../services/NOTIFICATION-API.md) | Bearer access token |
| GET | `/api/v1/notifications/preferences` | [notification](../services/NOTIFICATION-API.md) | Bearer access token |
| PATCH | `/api/v1/notifications/preferences` | [notification](../services/NOTIFICATION-API.md) | Bearer access token |
| GET | `/api/v1/notifications` | [notification](../services/NOTIFICATION-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
