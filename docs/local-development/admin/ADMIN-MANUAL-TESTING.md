# Manual admin acceptance / Postman

1. Run the isolated local infrastructure/migrations/start/seed documented in `../01-LOCAL-SETUP.md`. Sign in with the explicitly seeded owner using the real Identity request/verify endpoints. The development provider returns the code privately. Never paste tokens/OTP into shared reports. Registration remains invite-only.
2. In the admin browser verify Dashboard, current Organization and its tabs. Add/edit a local Branch/Team/unlinked Member. Confirm lifecycle actions before submitting. Invitations require an actual intended role UUID and a future expiry; the current contract has no phone/email recipient field or invitation-delivery mechanism. Do not claim this creates a new registered identity.
3. Verify Settings persists organization settings and own notification `push_enabled` / `notification_preview` (`FULL`, `SENDER_ONLY`, `NONE`). Own Devices/Sessions may be revoked after confirmation; current revocation logs you out. Notifications has no mark-read/unread/browser push.
4. Sign out, then sign in as the seeded normal member. Admin content must be rejected. In Postman repeat mutations with that token and expect 403. No token/invalid/expired tokens must fail; use known cross-tenant resource UUIDs and expect 404. Never forge production credentials.

## Postman

Import the existing `../postman/` collection and environment. Set Gateway base URL `http://localhost:8008`. Request OTP with `{ "phone_number": "<explicit seeded phone>", "purpose": "LOGIN" }`; verify with challenge/code and `device: { installation_id: "<uuid>", platform: "WEB", device_name: "Postman admin" }`. Store access/refresh variables privately. Identity returns organization_id/member_id.

GET `/api/v1/roles/` and `/api/v1/role-assignments/?member=<current-member-id>` to inspect actual role/permission assignments. OWNER/ADMIN/MANAGER/CUSTOM are backend roles; a role name alone is not authorization.

Organization GET/PATCH `/api/v1/organizations/current/` operates only the token's active tenant. Collection endpoints use trailing slash and cursor pagination with `page_size=10|20|50`, `cursor` from next/previous, fixed newest-first ordering. Search supported on members/branches/teams; status filters where documented. Do not assume a count or page-number endpoint.

For each route see ADMIN-API-ROUTES.md plus adjacent service OpenAPI JSON. Errors: 401 invalid/expired membership/token, 403 missing permission, 404 missing/cross-tenant ID, 400/422 invalid schema/lifecycle. Record actual responses locally, without Authorization values.

## Automated live workflow

`npm run test:live` uses actual browser UI and unmocked Gateway/backend requests. It is guarded to localhost, uses only development OTP for existing seeded users, never calls SMS/FCM, and writes sanitized `.local/admin-live-results.json`. Test resources remain in the isolated development database. Prepare the optional foreign tenant fixture using `scripts/prepare-live-fixtures.py` under `scripts/local/dev.py`'s Organization environment; it is restricted to 127.0.0.1:5434. It never grants frontend permissions.


## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
