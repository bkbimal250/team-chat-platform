# Email/password authentication

1. Sign in on admin http://localhost:3000/login or web chat http://localhost:3001 using a legitimate email/password account.
2. POST /api/v1/auth/login through Gateway must issue the existing tokens/session/device and select a real active membership. No OTP challenge is required.
3. Wrong password, unknown email, disabled Identity and OTP-only account without a password all produce generic INVALID_CREDENTIALS. No passwords/hashes appear in responses/logs.
4. Verify authenticated profile/current organization; Owner enters admin, ordinary Member is rejected by the admin role guard.
5. Refresh with the current refresh token; verify rotation and reuse protection. Sign out; protected routes must require authentication again.
6. With no session, chat/admin pages must not expose private data. Cross-tenant resource tests must retain backend enforcement.
7. Disabled phone OTP requests return PHONE_OTP_DISABLED and never call Vonage. Test rate limits by configuration/unit tests, not by exhausting counters.
8. QR/device/session flows remain available through the existing contracts.

[Full policy and exact Redis key limits](../onboarding/EMAIL-PASSWORD-AUTH.md). [Employee password setup](../onboarding/MEMBER-PASSWORD-ONBOARDING.md). Password reset and email verification are not implemented; do not simulate them.
