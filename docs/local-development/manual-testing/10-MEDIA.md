# Media

## Preconditions

Local only. Infrastructure and APIs ready. REST base http://localhost:8008; Admin3000, Web Chat3001. Owner/Employee tokens kept separate. No automatic paid provider calls, retries or destructive collection runs.

## Steps and expected results

Authorize conversation metadata, obtain upload capability, transfer disposable bytes to returned URL with exact content type/headers, complete, sign download and compare bytes. Never attach bearer tokens to storage URLs. Multipart signs actual part numbers, captures ETags, resumes/completes/aborts. Local filesystem signing does not verify production S3/CORS.

## Every applicable endpoint

| Method | Route | Service reference | Authentication |
|---|---|---|---|
| PUT | `/local-storage/{token}` | [media](../services/MEDIA-API.md) | Signed capability in URL |
| GET | `/local-storage/{token}` | [media](../services/MEDIA-API.md) | Signed capability in URL |
| GET | `/health/live` | [media](../services/MEDIA-API.md) | None at this layer |
| GET | `/health/ready` | [media](../services/MEDIA-API.md) | None at this layer |
| POST | `/api/v1/media/uploads` | [media](../services/MEDIA-API.md) | Bearer access token |
| POST | `/api/v1/media/multipart` | [media](../services/MEDIA-API.md) | Bearer access token |
| POST | `/api/v1/media/{media_id}/multipart/parts` | [media](../services/MEDIA-API.md) | Bearer access token |
| GET | `/api/v1/media/{media_id}/multipart` | [media](../services/MEDIA-API.md) | Bearer access token |
| POST | `/api/v1/media/{media_id}/multipart/complete` | [media](../services/MEDIA-API.md) | Bearer access token |
| DELETE | `/api/v1/media/{media_id}/multipart` | [media](../services/MEDIA-API.md) | Bearer access token |
| POST | `/api/v1/media/{media_id}/complete` | [media](../services/MEDIA-API.md) | Bearer access token |
| GET | `/api/v1/media/{media_id}/download` | [media](../services/MEDIA-API.md) | Bearer access token |
| DELETE | `/api/v1/media/{media_id}` | [media](../services/MEDIA-API.md) | Bearer access token |

## Request, response, errors and permissions

Use each linked service reference: exact body/schema constraints, headers/query/path fields, expected declared statuses, source-backed response fields and authorization. Replace placeholders with fixture IDs. GET after each mutation; check role/tenant failures. Destructive actions require disposable fixtures. Internal routes are direct operator-only, not public Gateway routes.

## Record evidence

Record status, label and sanitized correlation ID. Never capture OTP, token, full phone, authorization/cookies or signed URLs. Check audit/outbox and consumed projections without purging application queues.
