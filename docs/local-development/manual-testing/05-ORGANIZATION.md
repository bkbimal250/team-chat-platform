# Organization

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Use Owner token. GET current organization/settings; PATCH supported fields only and re-read. Inspect roles/permissions/assignments/audit logs. Current tenant only; platform-wide administration unavailable. Lifecycle changes use disposable organizations, never your only Owner fixture.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/api/v1/audit-logs/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/audit-logs/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/members/{id}/roles/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/organizations/current/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| PATCH | `/api/v1/organizations/current/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/organizations/current/lifecycle/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/organizations/current/settings/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| PATCH | `/api/v1/organizations/current/settings/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/permissions/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/role-assignments/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/roles/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/roles/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/roles/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
