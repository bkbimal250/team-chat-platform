# Admin real-API baseline

Verified locally on 2026-10-04. No AWS, Terraform, backend or production deployment changes were made for this integration.

## Screens and contracts

| Screen | Status | Actual behavior |
|---|---|---|
| Login/session | Real API | Development OTP, verification, rotating refresh, logout and permission guard |
| Dashboard | Partial | Real tenant resource counts (bounded pages explicitly qualified), recent audit; no invented global statistics |
| Organizations | Partial | Current organization only; view/update/settings. Global organization discovery and creation unavailable |
| Branches/Teams | Real API | Tenant-scoped lists, search, filters, cursors, forms and lifecycle confirmations |
| Members | Real API | Tenant membership create/update, lifecycle and role assignment. Creating a member does not create an Identity user |
| Invitations | Partial | Role/expiry creation and revocation. Contract has no phone/email recipient or delivery |
| Roles/Audit | Real API | Current tenant role permissions/assignments and audit records |
| Devices/Sessions | Partial | Authenticated user's devices/sessions and revocation; no cross-user administrative endpoint |
| Notifications | Partial | Real own notification list; unread/read actions unavailable |
| Settings | Partial | Organization flags/timezone and push/preview preferences; unsupported settings labelled |
| Conversations/System/Security | Unavailable | No invented administrative contracts or persistence |

## Architecture and security

All requests use the existing Gateway via a same-origin Next route handler. Internal cursor URLs are reduced to their API path; private redirects are rejected. No direct-service browser requests. API authorization remains backend-authoritative. Roles are derived from actual current-member assignments and permissions. Session tokens are held in memory/per-tab sessionStorage, not printed. A failed refresh clears the session; a resource 403 does not falsely log the user out. Mutation errors and confirmations remain visible. No production mock records or invented capabilities are used; test doubles remain inside tests.

## Verification

20 unit/component tests pass, covering API errors/refresh, login, permission guards, resource rendering, forms and confirmations. The local browser/API runner executed 42 passing assertions: real development OTP login, expired token rejection and rotation, tenant lists, organization update, branch create/edit/disable/activate, unlinked member/team creation, invitation create/revoke, settings, own devices/sessions/notifications, logout, normal-user rejection and foreign-tenant/device access rejection. No browser exceptions. Results and screenshot are in ignored `.local/admin-live-results.json` and `.local/admin-dashboard.png`; no tokens or OTP values are included in the report.

Run `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. Live checks are local-only (`npm run test:live`) and intentionally create/update isolated development fixtures; never use against production. Prepare foreign-tenant fixtures using `scripts/prepare-live-fixtures.py` through the local Organization runtime. Preserve OTP cooldown/rate limits.

## Accepted gaps

No platform-wide organization administration, global analytics, cross-user device administration, notification read state, or administrative conversation moderation contracts exist. Invitation delivery/onboarding must be addressed at the backend contract level rather than simulated in the UI. Existing main web/mobile applications are not modified.


## Final company onboarding verification (2026-10-04)

Full backend: 401 collected / 401 passed / 0 failed / 0 skipped. Admin: 24 collected / 24 passed / 0 failed. Lint, TypeScript and production build pass. Actual local browser/API onboarding: 20 passed / 0 failed; three physical service-owned DB checks pass. Identity migration reaches single head `0003_company_registration`; repeat upgrade succeeds. `/register` is active, returning LOGIN OTP restores the same organization/membership/profile, and existing admin permission tests remain green. No real SMS/FCM, AWS changes or production deployment.
