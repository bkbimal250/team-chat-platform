# Conversations

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Direct creation uses workspace member_id from people search. Group creation uses actual member_ids. List/detail/state, membership, promotion/demotion, ownership transfer and close enforce conversation roles. Tenant membership alone never grants access to all private conversations.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [conversation](../services/CONVERSATION-API.md) | None at this layer |
| GET | `/health/ready` | [conversation](../services/CONVERSATION-API.md) | None at this layer |
| POST | `/api/v1/conversations/direct` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/groups` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| GET | `/api/v1/conversations` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| GET | `/api/v1/conversations/{cid}` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/members` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| DELETE | `/api/v1/conversations/{cid}/members/{mid}` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/leave` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/close` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| GET | `/api/v1/conversations/{cid}/members` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/members/{mid}/promote` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/members/{mid}/demote` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{cid}/transfer-ownership` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| PATCH | `/api/v1/conversations/{cid}` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| PATCH | `/api/v1/conversations/{cid}/state` | [conversation](../services/CONVERSATION-API.md) | Bearer access token |
| POST | `/internal/v1/conversations/{cid}/authorize` | [conversation](../services/CONVERSATION-API.md) | Internal service token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
