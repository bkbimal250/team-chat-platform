# Messaging

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Wait for real conversation authorization projection. POST one message, retain actual client_message_id for retry dedupe. GET history with real pagination parameters. Recipient delivered/read updates unread and summaries; use recipient token. Edit/delete/reactions enforce actual membership/ownership. Do not bypass transient authorization403.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/health/live` | [messaging](../services/MESSAGING-API.md) | None at this layer |
| GET | `/health/ready` | [messaging](../services/MESSAGING-API.md) | None at this layer |
| POST | `/api/v1/conversations/{conversation_id}/messages` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| GET | `/api/v1/conversations/{conversation_id}/messages` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| PATCH | `/api/v1/messages/{message_id}` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| DELETE | `/api/v1/messages/{message_id}` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| POST | `/api/v1/messages/{message_id}/reactions` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| DELETE | `/api/v1/messages/{message_id}/reactions/{reaction}` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{conversation_id}/delivered` | [messaging](../services/MESSAGING-API.md) | Bearer access token |
| POST | `/api/v1/conversations/{conversation_id}/read` | [messaging](../services/MESSAGING-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
