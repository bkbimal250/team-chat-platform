# Password recovery

Identity exposes two public Gateway-routed endpoints:

- `POST /api/v1/auth/password/forgot` with `{ "email": "person@example.test" }`
- `POST /api/v1/auth/password/reset` with `{ "token": "…", "new_password": "12+ characters" }`

The forgot response is always the same, whether or not an eligible account exists. It is rate limited to 10 requests per IP and email per hour. Reset attempts are limited to 10 per IP per hour.

Reset tokens are opaque, generated with the existing cryptographic token helper, and stored only as a SHA-256 digest. They expire after `PASSWORD_RESET_TTL` seconds (900 by default), are single-use, and are never logged or returned by the production API.

For local development only, `APP_ENV=development` includes `development_reset_token` in every successful request response. Unknown or ineligible addresses receive an indistinguishable unusable token, preserving enumeration resistance. Use a valid local token only to form `http://localhost:3001/reset-password?token=<token>`; never copy it into committed files, logs, or production tooling.

A successful reset replaces the existing Argon2id password hash and revokes every active Identity session for that account, including refresh credentials. Existing access JWTs are rejected on their next authenticated Identity request because the service checks durable session status.
