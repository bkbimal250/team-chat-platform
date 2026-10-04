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