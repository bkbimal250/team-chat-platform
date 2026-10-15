# GlobalChat staging — manual E2E checklist

Run against a **staging** gateway + realtime deployment. Record pass/fail and correlation IDs for failures. Do not skip device setup or E2EE steps.

## Prerequisites

- [ ] Migrations applied (identity `0011`, messaging `0005`, media, conversation, organization).
- [ ] Two test accounts (A and B), each with at least one registered device after **device setup**.
- [ ] Flutter app built with correct `API_BASE_URL` and `REALTIME_WSS_URL`.
- [ ] Optional third device or emulator for multi-device / linked-devices tests.

## Personal chats

- [ ] Register or log in as **personal** user (JWT with no `organization_id` in `/auth/me`).
- [ ] Open or create personal direct chat (`POST /api/v1/conversations/personal/direct` path used by app).
- [ ] Send E2EE text; other party receives and decrypts.
- [ ] Force app background/foreground; history still decrypts after reopen.

## Organization / workspace

- [ ] Log in as **workspace** user (`organization_id` and `member_id` on `/auth/me`).
- [ ] `GET /api/v1/members/` returns colleagues for group picker (permissioned).
- [ ] Switch org via `POST /api/v1/auth/context` with a valid `organization_id` you belong to (may require operator-provided ID if UI only shows current org).
- [ ] After switch, conversation list reflects new tenant; personal token session is separate (sign in with personal account to verify personal chats still work).

## Direct messaging (workspace)

- [ ] E2EE 1:1 message A → B: delivered, decrypt OK.
- [ ] Reply to a message; preview visible.
- [ ] Edit own message; “Edited” shown.
- [ ] Delete own message; tombstone/deleted state.
- [ ] Add reaction; remove reaction; counts update after refresh/realtime.
- [ ] Read receipts: reader opens chat; sender sees delivered/read progression on own messages (realtime `message.delivered.v1` / `message.read.v1`).

## Group messaging

- [ ] Create workspace group; add members from org directory.
- [ ] Send group E2EE message; all members decrypt (may need sender-key distribution via message envelope + realtime).
- [ ] New member added; subsequent messages decrypt after distribution.
- [ ] Promote / remove / leave / delete (owner) flows succeed with API errors surfaced in UI on failure.

## Linked devices & trust

- [ ] Settings → **Linked devices**: list shows fingerprints from `GET /api/v1/users/{identity}/devices`.
- [ ] Simulate identity key change (new device or key rotation on test account): recipient sees **trust warning**, not plaintext.
- [ ] **Trust identity and reload** verifies remote device and message decrypts after refresh.
- [ ] Sender with missing recipient pre-keys sees send failure with clear error (recipient must open app / replenish keys).

## Sender-key distribution

- [ ] Group message from device 1; device 2 of another member decrypts without manual refresh (or after one refresh).
- [ ] Observe realtime `e2ee.sender_key_distribution.v1` on subscriber when sender publishes (optional: WSS logging proxy).

## Encrypted media

- [ ] Send image attachment; upload completes (`POST .../complete` after PUT).
- [ ] Recipient taps attachment; download + decrypt shows image (no file key on wire to backend).
- [ ] Failed upload or complete shows error; retry does not show fake success.

## Retries & resilience

- [ ] Failed send shows **Failed** + Retry; retry uses API again.
- [ ] Banner **Retry** on load/refresh errors refetches history.
- [ ] Disable network mid-chat; restore network; reconnect WSS; open chat triggers resync or manual refresh recovers history (`connection.resync_required.v1` or `message.created.v1`).

## Sign-off

| Area | Pass | Notes |
|------|------|-------|
| Personal | | |
| Workspace / org | | |
| Direct E2EE | | |
| Group E2EE | | |
| Trust / devices | | |
| Media | | |
| Realtime / resync | | |
