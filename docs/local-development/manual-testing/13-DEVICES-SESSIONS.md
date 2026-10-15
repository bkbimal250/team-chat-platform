# Devices and sessions

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

List own sessions/devices; inspect actual IDs. Revoke a second disposable session/device, check subsequent token behavior. Revoke current/other sessions only at the end. Cross-user device admin unavailable.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/api/v1/devices` | [identity](../services/IDENTITY-API.md) | Bearer access token |
| GET | `/api/v1/devices/{device_id}` | [identity](../services/IDENTITY-API.md) | Bearer access token |
| POST | `/api/v1/devices/{device_id}/revoke` | [identity](../services/IDENTITY-API.md) | Bearer access token |
| GET | `/api/v1/auth/sessions` | [identity](../services/IDENTITY-API.md) | Bearer access token |
| POST | `/api/v1/auth/sessions/{session_id}/revoke` | [identity](../services/IDENTITY-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
