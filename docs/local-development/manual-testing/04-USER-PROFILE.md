# User profile

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

GET me/preferences/privacy first, PATCH supported fields, re-read. Search workspace people; use returned member_id for direct chat. Block another local user by user_id, check blocked list/policy and unblock. Profile user_id and workspace member_id are distinct.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [user](../services/USER-API.md) | None at this layer |
| GET | `/health/ready` | [user](../services/USER-API.md) | None at this layer |
| POST | `/internal/v1/users/block-check` | [user](../services/USER-API.md) | Internal service token |
| POST | `/internal/v1/users/projections` | [user](../services/USER-API.md) | Internal service token |
| GET | `/api/v1/users/me` | [user](../services/USER-API.md) | Bearer access token |
| PATCH | `/api/v1/users/me` | [user](../services/USER-API.md) | Bearer access token |
| GET | `/api/v1/users/me/preferences` | [user](../services/USER-API.md) | Bearer access token |
| PATCH | `/api/v1/users/me/preferences` | [user](../services/USER-API.md) | Bearer access token |
| POST | `/api/v1/users/{user_id}/block` | [user](../services/USER-API.md) | Bearer access token |
| DELETE | `/api/v1/users/{user_id}/block` | [user](../services/USER-API.md) | Bearer access token |
| GET | `/api/v1/users/me/privacy` | [user](../services/USER-API.md) | Bearer access token |
| PATCH | `/api/v1/users/me/privacy` | [user](../services/USER-API.md) | Bearer access token |
| GET | `/api/v1/users/me/blocked` | [user](../services/USER-API.md) | Bearer access token |
| GET | `/api/v1/users/search` | [user](../services/USER-API.md) | Bearer access token |
| GET | `/api/v1/users/{user_id}` | [user](../services/USER-API.md) | Bearer access token |
| POST | `/internal/v1/users/company-owner` | [user](../services/USER-API.md) | Internal service token |
| POST | `/internal/v1/users/provision` | [user](../services/USER-API.md) | Internal service token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
