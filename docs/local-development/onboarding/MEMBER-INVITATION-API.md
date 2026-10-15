> Preserved phone OTP reference: disabled in the current primary flow. Use [email/password authentication](EMAIL-PASSWORD-AUTH.md) for normal local registration/login. Enable OTP explicitly only for future capability tests.

# Member invitation API

All public examples use `{{gateway_base_url}}=http://localhost:8008`. JSON Content-Type is required for POST bodies; authenticated calls also require `Authorization: Bearer {{access_token}}`. Never set browser-supplied tenant/inviter/acceptance fields. Optional empty branch/team selections must be JSON null or omitted, not empty strings. UUID placeholders must be replaced with actual tenant resources.

## POST /api/v1/invitations/

Purpose: Create a recipient-bound invitation.

Auth: Bearer + invitation.create. Role: Owner/Admin or delegable Manager.

Headers: `Content-Type: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
{"recipient_name":"Employee Name","recipient_phone":"{{employee_phone}}","recipient_email":"","intended_role_id":"{{role_id}}","branch_id":"{{branch_id}}","team_id":"{{team_id}}"}
```

Response: 201 invitation, transient development_url.

Errors: INVITATION_PENDING, MEMBER_ALREADY_EXISTS, ROLE_ESCALATION_DENIED, INVALID_EXPIRY, PHONE_INVALID, INACTIVE_MEMBERSHIP_TARGET, DELIVERY_UNAVAILABLE. Validation rejects unknown/read-only fields.

Used by screen: Admin Members -> Invitations -> Invite Member.

## GET /api/v1/invitations/?status=PENDING&page_size=20

Purpose: Tenant-scoped cursor list; status also accepts ACCEPTED/EXPIRED/REVOKED.

Auth: Bearer + invitation.view. Role: Backend permission.

Headers: `Accept: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
null
```

Response: 200 {results,next,previous}; no token/hash.

Errors: 401/403 permission failures. Validation rejects unknown/read-only fields.

Used by screen: Admin Invitations.

## GET /api/v1/invitations/{{invitation_id}}/

Purpose: Tenant-scoped detail.

Auth: Bearer + invitation.view. Role: Backend permission.

Headers: `Accept: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
null
```

Response: 200 invitation without token/hash.

Errors: 404 foreign/unknown ID. Validation rejects unknown/read-only fields.

Used by screen: Admin Invitations/Postman.

## POST /api/v1/invitations/{{invitation_id}}/resend/

Purpose: Rotate the pending recipient token.

Auth: Bearer + invitation.create. Role: Backend delegation.

Headers: `Content-Type: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
null
```

Response: 200 same invitation + transient development_url.

Errors: INVITATION_UNAVAILABLE, ROLE_ESCALATION_DENIED, INVITES_DISABLED. Validation rejects unknown/read-only fields.

Used by screen: Admin Resend.

## POST /api/v1/invitations/{{invitation_id}}/revoke/

Purpose: Revoke pending invitation; accepted membership unchanged.

Auth: Bearer + invitation.revoke. Role: Owner/Admin permission.

Headers: `Content-Type: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
null
```

Response: 200 REVOKED invitation.

Errors: INVITATION_NOT_PENDING, 404 foreign ID. Validation rejects unknown/read-only fields.

Used by screen: Admin Revoke confirmation.

## POST /api/v1/auth/invitations/validate

Purpose: Safely resolve an opaque invitation.

Auth: Public + per-IP rate limit. Role: Possession of opaque token.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"token":"{{invitation_token}}"}
```

Response: 200 {valid,company_name,recipient_name,recipient_phone_masked,expires_at}.

Errors: INVITATION_INVALID/EXPIRED/REVOKED/ACCEPTED/UNAVAILABLE, RATE_LIMITED. Validation rejects unknown/read-only fields.

Used by screen: Employee /join.

## POST /api/v1/auth/invitations/request

Purpose: Request OTP for the stored recipient; resume an existing verified intent without another OTP.

Auth: Public + existing OTP limits. Role: Possession of token.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"token":"{{invitation_token}}"}
```

Response: 202 {onboarding_id,expires_at,resend_after,development_code,verified}; development_code is null outside development.

Errors: Invitation failures, RATE_LIMITED, OTP_RESEND_COOLDOWN. Validation rejects unknown/read-only fields.

Used by screen: Employee Continue.

## POST /api/v1/auth/invitations/resend

Purpose: Request replacement OTP using the same authoritative token binding.

Auth: Public + existing OTP limits. Role: Possession of token.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"token":"{{invitation_token}}"}
```

Response: 202 same challenge schema, newly bound OTP or verified resume.

Errors: Invitation failures and cooldown. Validation rejects unknown/read-only fields.

Used by screen: Employee Resend code.

## POST /api/v1/auth/invitations/verify

Purpose: Verify bound OTP, complete saga and create normal session.

Auth: Public + challenge/code proof and attempt limit. Role: Recipient phone proof.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"onboarding_id":"{{onboarding_id}}","otp":"{{invitation_otp}}","device":{"installation_id":"{{installation_id}}","platform":"WEB","device_name":"Local Employee Browser"}}
```

Response: 200 normal TokenResponse access/refresh/session/device/organization/member.

Errors: OTP_INVALID/EXPIRED/REPLAYED/TOO_MANY_ATTEMPTS, invitation failures, ACCOUNT_UNAVAILABLE, PROVISIONING_RETRY. Validation rejects unknown/read-only fields.

Used by screen: Employee Verify and join workspace.

## GET /api/v1/members/{{employee_member_id}}/

Purpose: Verify active member and assignments; phone masked.

Auth: Bearer + member.view. Role: Current tenant membership.

Headers: `Accept: application/json`; `Authorization: Bearer {{access_token}}`.

Body / Postman example:
```json
null
```

Response: 200 member plus roles, branches, teams, recipient_phone_masked.

Errors: 404 foreign/unknown member. Validation rejects unknown/read-only fields.

Used by screen: Admin Members / Postman.

## POST /api/v1/auth/otp/request

Purpose: Returning employee normal login.

Auth: Public + existing OTP limits. Role: Existing phone policy.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"phone_number":"{{employee_phone}}","purpose":"LOGIN"}
```

Response: 202 challenge_id and local-only development_code.

Errors: Existing cooldown/rate/provider errors. Validation rejects unknown/read-only fields.

Used by screen: Web phone login.

## POST /api/v1/auth/otp/verify

Purpose: Returning employee normal session.

Auth: Public + OTP proof. Role: Active identity/membership.

Headers: `Content-Type: application/json`; no bearer required.

Body / Postman example:
```json
{"challenge_id":"{{login_challenge_id}}","code":"{{login_otp}}","device":{"installation_id":"{{installation_id}}","platform":"WEB","device_name":"Local Employee Browser"}}
```

Response: 200 existing organization/member normal TokenResponse.

Errors: OTP failures, REGISTRATION_NOT_ALLOWED, unavailable account. Validation rejects unknown/read-only fields.

Used by screen: Web login.

## Private service contracts (not Gateway/browser routes)

POST Organization `/api/internal/v1/invitations/validate/`: X-Internal-Service-Token; body {token}; returns authoritative invitation_id, organization_id, company_name, recipient_name, phone, expires_at to Identity only. No user role bypass.

POST Organization `/api/internal/v1/invitations/accept/`: same service auth; body {invitation_id,token_hash,phone,identity_id}; validates frozen binding, current inviter and targets, creates/reuses membership; returns {organization_id,member_id}. Idempotent only for the same accepted identity. Errors use sanitized invitation/permission/target categories.

POST Organization `/api/internal/v1/invitations/resume/`: same exact bound body; only an accepted invitation with matching identity and active member/tenant returns its snapshot. Identity calls this only for its own VERIFIED intent during bounded completion recovery. It is not a new public accepted-link grant.

POST User `/internal/v1/users/provision`: existing service auth; {identity_id,display_name}; returns {user_id}. Idempotent global profile creation, no existing-name overwrite. The previous company-owner endpoint remains available. Internal tokens must not be exported in Postman environments or browser code.
