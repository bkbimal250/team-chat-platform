# Company email/password registration

1. Run local readiness checks; all nine APIs must be ready. Confirm AUTH_EMAIL_PASSWORD_ENABLED=true and AUTH_PHONE_OTP_ENABLED=false.
2. Open http://localhost:3000/register. Use a NEW development email and disposable local company.
3. Enter Company name, Owner name, Email, retained Phone, Password (12–128 characters), Confirm password. Country/calling-code search remains available.
4. Mismatched confirmation must block submission. Click Create Company once.
5. Expect 201, real Identity, User profile, Organization, Owner membership/role and normal session. Expect the admin Dashboard; no OTP screen appears.
6. Confirm the current organization and Owner permissions through real APIs. Phone/email are not marked verified.
7. Sign out. Sign in using the same email/password. The same Identity, organization and member return.
8. Completed duplicate registration must show a controlled conflict. Interrupted provisioning retries must retain original IDs; see automated PostgreSQL tests.
9. Verify no new OTP challenge/provider request for this flow. Never log passwords/tokens or query private configuration values.

Exact requests/responses: [Identity API](../services/IDENTITY-API.md). [Saga and migration](../onboarding/COMPANY-EMAIL-REGISTRATION.md). Preserved older OTP guide is future/disabled, not this active flow.
