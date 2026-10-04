Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Local authentication
OTP_PROVIDER=development, APP_ENV=development, REGISTRATION_POLICY=invite_only. No SMS provider calls. Seed explicitly provisions +919000000001 (Alice) and +919000000002 (Bob), one local workspace and memberships. Seed is guarded to isolated 127.0.0.1:5434 databases; arbitrary signup remains blocked.

YOU DO THIS MANUALLY: Continue with phone, country 91, number 9000000001. Local development code is shown only in a development frontend configured with a loopback HTTP API and only when the backend returns development_code. Enter it normally. Production frontend does not display this helper.

Postman request: POST /api/v1/auth/otp/request with phone_number and purpose LOGIN. Verify: challenge_id, code, device {installation_id (>=16 characters), platform WEB, device_name}. Copy tokens privately. JWT RS256 issuer identity-service / audience team-chat-platform. Refresh rotates credentials; logout revokes session. Uninvited verification returns REGISTRATION_NOT_ALLOWED. No authentication bypass.
