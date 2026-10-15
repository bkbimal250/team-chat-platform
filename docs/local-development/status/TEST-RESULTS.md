# Email/password verification — 2026-10-05

Current authentication results supersede the historical records below. Email/password is primary; phone OTP is disabled locally and its implementations remain preserved. Identity migration `0005_email_password` applied to local PostgreSQL. All nine API live/ready checks passed, and admin/web chat are running on ports 3000/3001.

Affected backend regression: Organization 74, Identity 121, User 39, Gateway 33: **267 passed, 0 failed, 0 skipped**. Admin: **36 passed**. Web chat: **50 passed**. Both frontends passed lint, typecheck and production builds.

Live Gateway checks passed company registration, Owner profile/membership/session, returning login, refresh/logout, email-bound employee invitation/password setup, employee profile/login and invitation replay rejection. Browser checks passed company registration, returning Owner login, invitation creation, employee web-chat onboarding and normal-member admin rejection. No OTP challenge was created and no SMS was sent.

Email verification and password reset are not implemented. Existing OTP-only accounts require a legitimate password setup/recovery flow. Invitation email delivery is not configured; local development uses a private invitation link. See [authentication policy](../onboarding/EMAIL-PASSWORD-AUTH.md).

## Historical records

# Verified test results

Last verified: 2026-10-04. Real local PostgreSQL/RabbitMQ enabled.

| Service | Collected | Passed | Failed | Skipped |

|---|---:|---:|---:|---:|

| conversation-tests | 20 | 20 | 0 | 0 |

| gateway-tests | 18 | 18 | 0 | 0 |

| identity-tests | 64 | 64 | 0 | 0 |

| media-tests | 47 | 47 | 0 | 0 |

| messaging-tests | 71 | 71 | 0 | 0 |

| notification-tests | 50 | 50 | 0 | 0 |

| organization-tests | 33 | 33 | 0 | 0 |

| realtime-tests | 35 | 35 | 0 | 0 |

| user-tests | 37 | 37 | 0 | 0 |

Backend total: 375. Deselected: 0. Organization live broker integration: 1 collected / 1 passed. Tests labelled unit also include PostgreSQL-backed Notification repository/worker cases; these are not broker-free mocks.

Frontend: 36 collected / 36 passed / 0 failed / 0 skipped. npm ci, npm run lint, npm run typecheck, npm run build PASS. Service Ruff check/format PASS.

Live local smoke workflow: text send, Rabbit/Redis/WebSocket receive, duplicate submission, durable preview/unread, typing/timeout, delivered/read, reconnect, history/list PASS. Real image/video/audio/voice/PDF upload -> complete -> message -> recipient download PASS. Group create/promote/demote/remove/re-add/leave PASS. Profile/privacy/preferences/inbox/devices reads PASS. Missing-token/other-device checks PASS. Real User block/unblock events reach Messaging: blocked sends return 403; unblocking restores sending. QR authorize/consume/single-use/logout PASS.

Processes: 9 APIs + 15 workers, 24/24 running. 18 live/ready checks return 200. Application queues drained; audit/archive retain events intentionally. No real SMS/FCM sent.

Browser: initial frontend rendered in browser. Subsequent browser automation became unavailable. Full authenticated browser interaction, media playback, microphone/camera and responsive/offline checks require manual verification. API integration success is not proof of those UI/hardware checks.
# Current documentation verification â€” 2026-10-05

These results supersede historical runtime claims below; historical results are retained for context.

| Check | Result |
|---|---|
| Gateway full tests, service CORS defaults | 30 passed, 0 failed |
| Identity unit/contracts/security | 67 passed, 0 failed |
| Organization full test attempt | 1 passed, 71 setup errors: PostgreSQL connection timeout |
| Local health probes | 0/18 reachable; all returned URLError |
| Source import/OpenAPI export | All nine services exported successfully |
| Route inventory | 148 operations, 148 unique service/method/path combinations |
| Markdown links | 54 files checked, 0 broken local Markdown links |
| Postman collection/environment | Both JSON files parse successfully |

The first Gateway run inherited local-only CORS origins and failed its production-origin test (29 passed/1 failed). Removing that test-environment override, without changing application configuration or source, produced 30/30 passing tests. No production/provider credentials were used in tests. Database-backed suites for the remaining services were not run after the Organization infrastructure failure. No SMS/FCM, migration, seed, AWS or Terraform action occurred.
