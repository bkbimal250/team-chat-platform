# Email verification

Identity keeps email verification separate from login, password recovery, invitations, and phone verification.

## API

- `POST /api/v1/auth/email/verify` consumes `{ "token": "…" }` once.
- `POST /api/v1/auth/email/verification/resend` accepts `{ "email": "…" }` and always returns the same generic success message for eligible and unknown accounts.
- `GET /api/v1/auth/me` exposes only the signed-in identity's `email`, `email_verified`, and `email_verified_at` fields.

Verification challenges are random opaque values. Identity stores only a SHA-256 digest, expires them after `EMAIL_VERIFICATION_TTL` (24 hours by default), and consumes all prior active challenges whenever a new one is issued. Resends are rate-limited to 10 per hour for both the requesting IP and a digest of the canonical email address.

## Local workflow

With `APP_ENV=development`, the resend response contains a development-only verification token. Use it only on a local machine:

1. Register or sign in normally; login remains allowed while unverified.
2. Request a resend.
3. Open `/verify-email?token=<development token>` in the local web app.

No real email is sent locally or by this implementation. Staging and production responses never expose a raw token.

## Migration policy

Migration `0008_email_verification` adds a nullable timestamp and the challenge table. Existing accounts remain at their existing boolean value; accounts without prior proof stay unverified. The migration is reversible for schema objects, but a downgrade intentionally cannot reconstruct verification timestamps after dropping the column.

Password reset remains independent and does not verify an email. Invitation acceptance also does not verify an email; it creates a separate verification challenge for an unverified identity. Email address change is not currently implemented, so there is no email-change verification flow in this phase.
