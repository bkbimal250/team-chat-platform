# Email/password authentication

PRIMARY NOW: Email + Password. PRESERVED FOR FUTURE: Phone + OTP.

The local runner enables `AUTH_EMAIL_PASSWORD_ENABLED=true` and sets `AUTH_PHONE_OTP_ENABLED=false`. Identity owns the authoritative login email and nullable `password_hash`. User profiles remain a separate domain; their profile fields are not an alternate authentication lookup. Email is trimmed, validated with email-validator, normalized (including the domain), then lowercased for consistent case-insensitive login. No Gmail dot/plus or mailbox-provider alias rules are applied. A unique PostgreSQL expression index on `lower(trim(email))` prevents case/whitespace duplicates, including historical addresses.

New passwords use the existing Argon2id library: 12–128 characters, including spaces and symbols, without truncation. Passwords and hashes are never returned or logged. Existing OTP-only identities retain a NULL password hash; generic password authentication fails until a legitimate credential setup/recovery mechanism exists. No passwords are silently assigned or existing accounts deleted.

`POST /api/v1/auth/login` accepts email, password, the existing device payload and optional organization_id. It authenticates the existing Identity, uses a personal context for completed personal registrations, checks active Organization memberships for workspace contexts, and uses the same SessionService, RS256 JWT, refresh rotation, devices, context switching and logout as OTP. Wrong password, unknown email, disabled Identity and missing password all return `401 INVALID_CREDENTIALS` with “Invalid email or password.” No account-specific explanation is exposed.

## Rate limits

Redis database 0 stores server-side counters. Password login: `password:login:ip:{ip}` 30/hour; `password:login:email:{sha256(canonical_email)}` 20/hour. Registration/password invitation setup: corresponding `password:register:*` keys, 10/hour per IP and email. Rejections return `429 RATE_LIMITED` with details.retry_after. These are separate from the preserved OTP counters. Do not FLUSHDB or exhaust a limit to verify it.

## Verification and recovery policy

EMAIL LOGIN ENABLED. EMAIL VERIFICATION NOT YET REQUIRED/IMPLEMENTED. Company registration leaves email_verified and phone_verified false. Typed phone numbers are retained without being treated as proof. Employee invitation tokens are private capabilities, bound to the authoritative invited email and assignments; they do not mark email as verified.

PASSWORD RESET: NOT IMPLEMENTED. Supplying an email address never resets a password. Existing email/password accounts accepting another invitation must supply their current password, which is never replaced. OTP-only accounts cannot acquire a password merely by claiming an existing email.

## Preserved phone OTP

DevelopmentOTPProvider, HiliteSMSOTPProvider, VonageVerifyOTPProvider, phone normalization, challenges, migrations, rate limits and tests remain. Disabled phone requests return `403 PHONE_OTP_DISABLED` before calling a provider. Optional OTP UI components are retained separately from active login/registration. Enabling phone OTP is an explicit operator action; never assume APP_ENV alone prevents SMS. Legacy tests opt in to the preserved capability, while new email tests explicitly disable it and assert provider send counters remain zero.

See [Identity contracts](../services/IDENTITY-API.md), [company registration](COMPANY-EMAIL-REGISTRATION.md), [member setup](MEMBER-PASSWORD-ONBOARDING.md) and [manual authentication](../manual-testing/03-AUTHENTICATION.md).
