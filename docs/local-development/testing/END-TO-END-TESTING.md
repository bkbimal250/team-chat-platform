Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Real local workflow
Run infrastructure/migrate/start/seed first. Authenticate both explicit users via Postman or two browsers. The local automated scripts keep session tokens in ignored .local/sessions.json and never print them.

```powershell
services/realtime-service/.venv/Scripts/python.exe scripts/local/login_seed.py
services/realtime-service/.venv/Scripts/python.exe scripts/local/smoke.py
services/realtime-service/.venv/Scripts/python.exe scripts/local/feature_smoke.py
```
login_seed.py obtains two development-only OTP sessions privately. smoke.py requires those two local sessions; it refreshes them, creates/opens a direct chat, sends real text, receives Rabbit/Redis/WebSocket event, checks idempotency, typing, receipts and reconnect. feature_smoke.py uses fixtures under .local/fixtures and validates real attachments/groups/settings/QR. Results .local/smoke-results.json. These scripts modify only explicitly local test data.

YOU DO THIS MANUALLY: log in Alice in normal browser, Bob in private browser; select workspace people, open direct conversation, send text and each file type; verify live recipient rendering, unread/preview, read receipts. Reload to verify persistence. Toggle offline and reconnect. Test narrow mobile window and keyboard focus.


## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.


## Secure employee onboarding (2026-10-05)

The real two-context invitation/chat runner is node scripts/test-invitation-live.mjs from the admin app. It covers Owner invite -> Employee OTP -> normal session -> text/realtime/typing/receipts/unread/preview -> returning login -> revoke denial. Uses local Gateway and Rabbit only. See ../onboarding/MEMBER-INVITATION-TESTING.md.
