# Company registration API

Gateway base: `http://localhost:8008`. Admin UI: `http://localhost:3000/register`.

## Start

`POST /api/v1/auth/registration/company/start` (public, rate limited)

```json
{"company_name":"Development Company","owner_name":"Development Owner","email":"owner@example.com","phone":"+919000000003"}
```

202 response: `registration_id`, `expires_at`, `resend_after`, and `development_code` only with the development provider. Do not log/share codes. No organization, identity or membership is created yet.

## Verify

`POST /api/v1/auth/registration/company/verify` (public, rate limited)

```json
{"registration_id":"SERVER_UUID","otp":"RECEIVED_CODE","device":{"installation_id":"CLIENT_UUID_AT_LEAST_16_CHARACTERS","platform":"WEB","device_name":"GlobalChat Admin Browser"}}
```

200: normal Identity TokenResponse (`access_token`, `refresh_token`, `expires_in`, `session_id`, `device_id`, `organization_id`, `member_id`, `token_type`). Keep tokens private. Unknown fields, including organization_id and resubmitted registration details, are rejected.

## Resend

`POST /api/v1/auth/registration/company/resend`

```json
{"registration_id":"SERVER_UUID"}
```

202 replaces the authoritative OTP challenge and expiry; existing cooldown/rate limits apply. Verified provisioning must resume rather than resend. Expired unverified registrations can start anew.

## Errors

422 invalid input/phone; 409 ACCOUNT_EXISTS, REGISTRATION_PENDING, REGISTRATION_COMPLETED, OTP_REPLAYED; 400 OTP_INVALID/OTP_EXPIRED; 410 REGISTRATION_EXPIRED; 404 REGISTRATION_INVALID; 429 RATE_LIMITED/OTP_RESEND_COOLDOWN/OTP_TOO_MANY_ATTEMPTS; 503 PROVISIONING_RETRY. Responses contain safe categories, no raw provider response or submitted sensitive values.

## Private service contracts

Identity -> User: `POST /internal/v1/users/company-owner` with identity_id/display_name. Identity -> Organization: `POST /api/internal/v1/company-registration/` with organization_id/identity_id/company_name/owner_name/email. Both require the existing internal service token, use their own DB transaction and are idempotent. Browsers must never call these endpoints.

Returning login uses existing `/api/v1/auth/otp/request` (purpose LOGIN), `/api/v1/auth/otp/verify`, `/api/v1/auth/logout`; authenticated profile `/api/v1/users/me`, organization `/api/v1/organizations/current/`, roles `/api/v1/roles/`, assignments `/api/v1/role-assignments/?member=MEMBER_ID`.
