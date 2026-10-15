# Personal account foundation — 2026-10-08

Personal registration/session/self-service is implemented without an organization. Company onboarding and platform authorization are retained. Contacts, personal messaging and existing-user company creation remain future phases. Password recovery and email verification are implemented; older statements below are historical. See [personal accounts](../PERSONAL-ACCOUNTS.md) and [gap audit](../FINAL-PRODUCT-GAP-AUDIT.md).

# Email/password verification — 2026-10-05

Current authentication results supersede the historical records below. Email/password is primary; phone OTP is disabled locally and its implementations remain preserved. Identity migration `0005_email_password` applied to local PostgreSQL. All nine API live/ready checks passed, and admin/web chat are running on ports 3000/3001.

Affected backend regression: Organization 74, Identity 121, User 39, Gateway 33: **267 passed, 0 failed, 0 skipped**. Admin: **36 passed**. Web chat: **50 passed**. Both frontends passed lint, typecheck and production builds.

Live Gateway checks passed company registration, Owner profile/membership/session, returning login, refresh/logout, email-bound employee invitation/password setup, employee profile/login and invitation replay rejection. Browser checks passed company registration, returning Owner login, invitation creation, employee web-chat onboarding and normal-member admin rejection. No OTP challenge was created and no SMS was sent.

Email verification and password reset are not implemented. Existing OTP-only accounts require a legitimate password setup/recovery flow. Invitation email delivery is not configured; local development uses a private invitation link. See [authentication policy](../onboarding/EMAIL-PASSWORD-AUTH.md).

## Historical records

Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Implementation status
Working real local baseline: Docker infrastructure, seven migrated domain databases, nine APIs, fifteen workers, explicit invite-only seed, Gateway routing, text/realtime/typing/receipts, private local attachments. Source repairs address initial migration duplication, durable User outbox state, membership contract compatibility, Windows signal handling, persistent consumer event loops, async Redis consumer wiring, Pika thread ownership, first receipt counters and group rejoin.

API references are generated from actual running OpenAPI. Routes marked PARTIAL in master inventory are schema-verified but not individually mutation-tested. Do not treat documentation existence as execution proof. Full live result and regression counts are in TEST-RESULTS.md.
# Documentation refresh â€” 2026-10-05

Nine source-backed service references, OpenAPI exports, 148 unique method/path operations, fourteen ordered manual-testing chapters and Postman templates are available. Hidden internal/signed-transfer endpoints and WebSocket frames are documented separately from public OpenAPI contracts. Existing onboarding/admin guides are preserved. This is a documentation update, not an application implementation or deployment.

Current runtime verification supersedes earlier running-state claims: all eighteen local live/ready probes returned URLError because the services were unavailable during this task. PostgreSQL-backed Organization tests hit connection timeouts. See [current results](TEST-RESULTS.md); no missing API is represented by mock functionality.
