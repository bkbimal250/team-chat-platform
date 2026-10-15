# Health checks

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

GET /health/live and /health/ready directly on ports8000–8008. Compare Gateway and Admin bridge /api/gateway/health/ready. Expect200;503 identifies dependency failure. Empty registration JSON returns422 without sending OTP.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [organization](../services/ORGANIZATION-API.md) | None at this layer |
| GET | `/health/ready` | [organization](../services/ORGANIZATION-API.md) | None at this layer |
| GET | `/health/live` | [identity](../services/IDENTITY-API.md) | None at this layer |
| GET | `/health/ready` | [identity](../services/IDENTITY-API.md) | None at this layer |
| GET | `/health/live` | [user](../services/USER-API.md) | None at this layer |
| GET | `/health/ready` | [user](../services/USER-API.md) | None at this layer |
| GET | `/health/live` | [conversation](../services/CONVERSATION-API.md) | None at this layer |
| GET | `/health/ready` | [conversation](../services/CONVERSATION-API.md) | None at this layer |
| GET | `/health/live` | [messaging](../services/MESSAGING-API.md) | None at this layer |
| GET | `/health/ready` | [messaging](../services/MESSAGING-API.md) | None at this layer |
| GET | `/health/live` | [media](../services/MEDIA-API.md) | None at this layer |
| GET | `/health/ready` | [media](../services/MEDIA-API.md) | None at this layer |
| GET | `/health/live` | [notification](../services/NOTIFICATION-API.md) | None at this layer |
| GET | `/health/ready` | [notification](../services/NOTIFICATION-API.md) | None at this layer |
| GET | `/health/live` | [realtime](../services/REALTIME-API.md) | None at this layer |
| GET | `/health/ready` | [realtime](../services/REALTIME-API.md) | None at this layer |
| GET | `/health/live` | [gateway](../services/GATEWAY-API.md) | None at this layer |
| GET | `/health/ready` | [gateway](../services/GATEWAY-API.md) | None at this layer |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
