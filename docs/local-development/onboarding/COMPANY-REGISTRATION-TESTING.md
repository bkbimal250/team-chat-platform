# Company onboarding testing

Use isolated local infrastructure only. No real SMS/FCM or production data changes.

1. Run `python scripts/local/dev.py infra`, then local migrations and `start`. Verify nine API health endpoints and tracked workers.
2. Start the existing admin application on 3000. Open `/register`.
3. Enter a clearly development-only company/owner/email and valid international phone not already registered.
4. Request registration OTP. Privately read the development_code from the response (development UI also displays it in development mode).
5. Verify with registration_id/code/device. Confirm the owner reaches Dashboard with the real company.
6. GET profile, current organization, members, roles and current-member role assignments through Gateway using the private token.
7. Confirm OWNER has existing backend administration permissions. Foreign organization resources must not be visible.
8. Repeat verification: it must reject completion and not create another company. Start with duplicate phone/email: reject.
9. Logout, request LOGIN OTP, verify normally. Confirm the same organization/member/profile IDs.
10. Verify a normal read-only member remains rejected by the admin guard and backend mutation permissions.

Automated browser/API sequence: `node scripts/test-company-live.mjs` from admin app. It uses actual local endpoints and DevelopmentOTPProvider, never logs OTP/phone/tokens, creates development records and writes sanitized results to ignored `.local/company-registration-results.json`. Do not rerun unnecessarily: normal OTP cooldowns/rate limits remain active.

Physical DB checks: `scripts/local/company_database_checks.py`, run via each owning service's local runtime, verify one identity, organization, owner membership and profile for the completed registration. No service writes another service database.

Backend tests cover input normalization/validation, duplicate contacts, expiration, failed attempt persistence, locked OTP, guessing, unknown/tampered fields, cooldown/resend, replay, concurrent start/verify, partial User/Organization failure, local recovery after expiry, User provisioning plus event redelivery, Organization transaction rollback/idempotency/owner role, and Gateway forwarding. Existing permission/tenant tests remain mandatory.

Run full backend with `python scripts/local/dev.py tests`. Admin: `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. New migration must be applied locally before live tests. Recovery procedure is in COMPANY-REGISTRATION.md. Email verification and invitation delivery are not implemented by this phase.


## Final company onboarding verification (2026-10-04)

Full backend: 401 collected / 401 passed / 0 failed / 0 skipped. Admin: 24 collected / 24 passed / 0 failed. Lint, TypeScript and production build pass. Actual local browser/API onboarding: 20 passed / 0 failed; three physical service-owned DB checks pass. Identity migration reaches single head `0003_company_registration`; repeat upgrade succeeds. `/register` is active, returning LOGIN OTP restores the same organization/membership/profile, and existing admin permission tests remain green. No real SMS/FCM, AWS changes or production deployment.
