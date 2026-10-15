> Preserved phone OTP reference: disabled in the current primary flow. Use [email/password authentication](EMAIL-PASSWORD-AUTH.md) for normal local registration/login. Enable OTP explicitly only for future capability tests.

# Invitation testing and manual workflow

## Local preparation

Start Docker Desktop, then from the existing repository run `python scripts/local/dev.py infra`, `python scripts/local/dev.py migrate`, `python scripts/local/dev.py start`. Credentials remain in ignored .local; never print/export them. PostgreSQL 5434, Redis 6380 and RabbitMQ 5672 are isolated local services. The corrected process check refuses to confuse a reused Windows PID with a running service.

Run admin on http://localhost:3000 and main web on http://localhost:3001: `npm run build` then `npm run start -- --hostname 127.0.0.1 --port 3000` (admin) or 3001 (web). The web environment points to Gateway http://localhost:8008 and realtime ws://localhost:8007. Local runner explicitly permits both frontend origins. Do not use production OTP settings.

## Automated coverage

Organization `tests/test_employee_invitations.py`: real PostgreSQL recipient/token hashing, expiration, replay, rotation/revoke, duplicate pending/active recipients, multi-tenant phones, Owner/Admin/Manager/Member permission cases, cross-tenant lookup/targets/revocation, immutable authority input, legacy accept bypass prevention, real parallel acceptance and production delivery fail-closed.

Identity `tests/integration/test_invitation_onboarding.py`: real PostgreSQL challenges/sagas/sessions with internal HTTP adapters controlled only in tests. Covers new/existing identities, public masked response, all authority tampering, invalid/revoked/expired/accepted tokens, wrong/expired/replayed OTP, committed attempt limits/cooldown, revoke/rotation after OTP, durable failure retry and parallel verification. Recovery test simulates acceptance committed before session completion, then reopens/re-requests without another OTP and resumes the same intent.

User existing profile-provisioning test now exercises both company-owner and general provision contracts, existing-name preservation and duplicate Identity event redelivery. Gateway ownership tests prove public invitation routes reach Organization/Identity and private acceptance/profile contracts are not forwarded. Existing conversation/block/tenant and Rabbit consumer idempotency suites remain mandatory.

Frontend tests: admin `tests/invitations.test.tsx` exercises creation, actual resource selections, masking, permissions, resend, revoke confirmation and server errors. Web `tests/invitation.test.tsx` exercises minimal bound payloads, session/navigation, safe error categories, code failures and StrictMode fragment cleanup.

Run affected backend suites through the existing local dev.run adapter, then all nine backend suites. For Organization use pytest --reuse-db against the isolated test DB to avoid interactive recreation after a failed concurrency test. Run tests/lint/typecheck/build in both frontend folders. No tests target AWS or production.

## Real browser runner

From admin run `node scripts/test-invitation-live.mjs`. It uses separate Owner and Employee browser contexts, real DevelopmentOTPProvider, Gateway APIs, Rabbit outboxes/consumers, normal sessions and actual chat UI. It creates isolated local branch/team/invitation fixtures, sends local text in both directions, verifies actual websocket frames/typing/receipts, durable unread/preview, logout/returning login, accepted replay and revoked onboarding denial. It waits for Messaging authorization projections rather than bypassing their fail-closed 403. No browser/API responses containing OTP/token/phone are printed. A genuine owner session may be reused from ignored .local after a runner interruption to avoid sending unnecessary replacement OTPs. Results contain only PASS/FAIL; auth cache is ignored and must never be committed/exported.

## YOU DO THIS MANUALLY

A. Owner/Admin browser: open http://localhost:3000/login and use an existing local Owner phone. Request the local code and verify. Members -> Invite Member. Enter employee name/international phone, optional email, actual role and optional branch/team. Create. Copy the Development-only invitation link privately. Refresh Invitations and confirm PENDING. Resend rotates the link; the old link must fail. Members displays the accepted role/branch/team and masked phone.

B. Employee Incognito: open that link on http://localhost:3001/join. Confirm company, invited name and masked phone. Request invitation code; use only the visibly labelled local development code. Verify and join. Chat opens. Do not change phone/role/tenant in a request. Owner and employee use People to create a direct conversation and exchange text. Observe typing, delivery/read and list preview/unread. Log out, then use normal phone OTP login and confirm the same membership. Reopen an accepted link: sign-in message, no new account. For a second invite, revoke in Admin with confirmation; incognito link must show revoked and create no membership.

C. Postman: import existing GlobalChat-Local collection/environment and use the MEMBER INVITATION folder. Set actual tenant role_id/branch_id/team_id and private temporary invitation_token extracted from the URL fragment. Create/list/detail/validate/request/verify/get-member/returning-login use the documented exact APIs. Keep Owner and Employee bearer tokens separate; do not overwrite an Owner session unintentionally. OTP and invite/token/access/refresh variables are blank secret-typed in the checked-in environment. Never export populated secrets. Cooldown is 60 seconds; failed attempts and rate limits are real. No automatic SMS/resend loops.

D. RabbitMQ Management: http://localhost:15672. Use the local globalchat_local account configured privately by the runner; do not copy its password into docs/collections. Inspect organization.events, identity.events, user.events, conversation events and consumers/outbox queues for drainage/redelivery. Do not purge queues. Useful application queues include messaging.authorization, conversation projections, notification consumers and realtime consumers. Read actual queue names from the management UI.

## Recovery and accepted limitations

Reopen the original fragment link after a browser refresh; secrets are intentionally not saved. Unverified continuation must respect the OTP cooldown. Verified continuation reuses the same intent/code for up to 30 minutes; after that, administrator/operator intervention may be required for an interrupted service-owned saga. Do not reactivate suspended/removed membership with a new invitation. Paid production delivery and multiple-active-organization selection UX remain future work; existing single-context JWT/context switching is preserved.


## Final local verification — 2026-10-05

- Backend: 472 passed, 0 failed, 0 skipped (Organization 72, Identity 108, User 39, Conversation 20, Messaging 71, Media 47, Notification 50, Realtime 35, Gateway 30).
- Admin: 30 passed; web chat: 47 passed. Both lint, typecheck and production build pass.
- Real local browser/API/Rabbit workflow: 53/53 assertions pass. Physical PostgreSQL persistence: 12/12 assertions pass.
- Organization invitations `0002_recipient_onboarding` and Identity `0004_invitation_onboarding` applied locally; repeat migration succeeds.
- Existing-identity reuse, role/tenant boundaries, parallel acceptance, outbox rollback and bounded interrupted-provisioning recovery have executable regression coverage.
- No AWS/Terraform/production changes; no real SMS, email or FCM.
