# Branches, teams and members

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Create same-tenant branch/team; GET list/detail, PATCH, re-read. Membership commands require actual member/membership IDs as declared. Role delegation is server-authoritative. Test forbidden cases with ordinary member and another tenant. Invite employees through verified onboarding, not fabricated active membership.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| GET | `/api/v1/branches/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/branches/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/branches/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| PATCH | `/api/v1/branches/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/branches/{id}/lifecycle/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/branches/{id}/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/branches/{id}/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/branches/{id}/members/{membership_id}/leave/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/branches/{id}/members/{membership_id}/primary/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/members/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| PATCH | `/api/v1/members/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/members/{id}/lifecycle/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/members/{id}/roles/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/teams/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/teams/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/teams/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| PATCH | `/api/v1/teams/{id}/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/teams/{id}/lifecycle/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| GET | `/api/v1/teams/{id}/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/teams/{id}/members/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |
| POST | `/api/v1/teams/{id}/members/{membership_id}/leave/` | [organization](../services/ORGANIZATION-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
