# GlobalChat — Full Project Documentation

Production domains: `api.michat.in` (HTTPS JSON API) • `ws.michat.in` (WebSocket realtime)
Last compiled: 2026-10-15, verified against source code.

---

## Table of Contents

1. [What the project is](#1-what-the-project-is)
2. [Domain concepts](#2-domain-concepts)
3. [Repository structure](#3-repository-structure)
4. [Backend architecture](#4-backend-architecture)
5. [The Gateway — how services connect](#5-the-gateway--how-services-connect)
6. [Service catalog](#6-service-catalog)
7. [Data models per service](#7-data-models-per-service)
8. [Complete API reference](#8-complete-api-reference)
9. [Realtime WebSocket protocol](#9-realtime-websocket-protocol)
10. [Event pipeline (Outbox → RabbitMQ → Consumers)](#10-event-pipeline)
11. [Authentication & security](#11-authentication--security)
12. [External integrations](#12-external-integrations)
13. [Frontend system](#13-frontend-system)
14. [Configuration](#14-configuration)
15. [Deployment](#15-deployment)
16. [Testing](#16-testing)
17. [Local development](#17-local-development)
18. [Known gaps](#18-known-gaps)

---

## 1. What the project is

GlobalChat is a Slack/Teams-style **team chat platform** built as a microservice monorepo:

- **9 Python backend services** — one API gateway + 8 domain services, each with its own PostgreSQL database, communicating synchronously through the gateway (HTTP) and asynchronously through RabbitMQ (domain events).
- **3 frontend apps** — Next.js web chat app, Next.js admin console, Flutter mobile app.
- **Shared infrastructure** — PostgreSQL 16, Redis 7, RabbitMQ 4, S3 (production) / local filesystem (development).

Product scope: companies register and invite members; members are organized into branches and teams; users chat via direct/group conversations (org-scoped or personal) with realtime delivery, media attachments, reactions, read receipts, push notifications, and a platform admin console.

---

## 2. Domain concepts

| Concept | Meaning |
|---|---|
| **Organization (company)** | The tenant. Owns settings, branches, teams, roles, audit logs. |
| **Branch / Team** | Org-structure units, each with their own memberships. |
| **Member** | A user's presence inside one organization. JWTs carry an `(org, member)` pair. |
| **Personal account** | Tenant-independent identity. Users have a personal space (personal contacts, DMs, groups) and can additionally create/join companies. |
| **Conversation** | `direct` or `group`; org-scoped or personal; has members, per-member state (mute/read cursors), settings. |
| **Message** | Ordered per-conversation via `ConversationSequence`. Supports edits, deletes, reactions, delivered/read receipts. |
| **Media** | Bytes uploaded out-of-band (presigned S3 in prod, local filesystem in dev); messages only carry metadata references. |
| **Identity verification** | Email/password is primary. Phone OTP (Vonage/SMS) implemented but disabled by default. QR deep-link login pairs mobile devices. |
| **Invitation** | Invite-only registration policy. Token-hashed invitations with expiry. |
| **Platform admin** | Super-admin/operator role governing the whole platform (separate from org owners/admins). |

---

## 3. Repository structure

```
team-chat-platform/
├── services/                     9 backend services (Python 3.12, uv-managed)
│   ├── organization-service/     Django 5.2 + DRF          :8000
│   ├── identity-service/         FastAPI                    :8001
│   ├── user-service/             FastAPI                    :8002
│   ├── conversation-service/     FastAPI                    :8003
│   ├── messaging-service/        FastAPI                    :8004
│   ├── media-service/            FastAPI                    :8005
│   ├── notification-service/     FastAPI                    :8006
│   ├── realtime-service/         FastAPI + native WS        :8007
│   └── gateway-service/          FastAPI reverse proxy      :8008
├── apps/
│   ├── web/web-chat-app/         Next.js 16 + React 19 end-user chat app
│   ├── admin-web/admin-webchat-app/  Next.js platform admin console
│   └── mobile/globalchatapp/     Flutter mobile app
├── packages/                     api-contracts, event-contracts, observability (empty scaffolds)
├── infrastructure/               postgres/init (creates 7 DBs), aws/s3-media (retired), terraform/
├── deploy/hostinger/             PRODUCTION stack: docker-compose.yml + Caddyfile + migrate scripts
├── docs/                         topology, event contracts, local-dev, manual-testing guides
├── scripts/local/dev.py          managed local runner (services, workers, migrate, seed, smoke)
├── tests/cross_service/          cross-service event-contract tests
├── docker-compose.yml            local dev stack (partial)
└── docker-compose.local.yml
```

---

## 4. Backend architecture

The one-line flow (docs/local-development/architecture/LOCAL-ARCHITECTURE.md):

> Browser → Gateway 8008 → domain APIs. WebSocket → Realtime 8007.
> PostgreSQL transactional write + outbox → RabbitMQ → idempotent projections / Realtime → shared Redis routing → recipient sockets.

### 4.1 Architectural pattern

- **API Gateway pattern** — the only public HTTP entrypoint is gateway-service :8008. It regex-routes `/api/v1/**` to the owning service (see §5). The gateway holds no database.
- **Database-per-service** — 7 PostgreSQL databases, one per stateful domain service. No cross-service SQL joins; cross-service reads happen via projections or internal HTTP calls.
- **Transactional outbox** — every domain write commits its rows and an `outbox_events` row atomically. A publisher worker (`SELECT … FOR UPDATE SKIP LOCKED`, publisher confirms) publishes to RabbitMQ with at-least-once semantics, exponential backoff `min(2^n, 3600s)`, 10 retries, DLX `organization.dead` → dead-letter + archive queues.
- **Idempotent consumers** — every consumer deduplicates via a `ProcessedEvent` inbox table before applying a change.
- **Projections** — services subscribe to each other's events to maintain local read models (member lists, block lists, phone digests, conversation summaries), avoiding synchronous cross-service reads on hot paths.
- **Shared Redis** — OTP/rate limits, realtime presence + subscription registry, gateway rate limiting.
- **WebSocket is separate** — the gateway never proxies WebSocket; clients connect directly to realtime-service :8007.

### 4.2 Request flow (HTTP)

```
Browser/App
    │  https://api.michat.in  (Caddy TLS in prod)
    ▼
gateway-service :8008
    │  match path → route owner
    │  rate-limit (Redis) → header allowlist → forward (httpx)
    ▼
domain service :800x
    │  verify JWT (shared public key)
    │  authorize (org/member pair, roles, membership)
    ▼
its own PostgreSQL  ──atomically──▶  outbox_events
                                         │  outbox publisher worker
                                         ▼
                                    RabbitMQ topic exchange
                                         │  consumers in other services
                                         ▼
                          projections / realtime fanout / push delivery
```

### 4.3 Request flow (WebSocket)

```
Client ── ws://…/api/v1/realtime?token=<access JWT> ──▶ realtime-service :8007
    authenticate → subscribe to conversations
    RabbitMQ consumer feeds domain events → Redis registry (cross-instance)
    → per-connection asyncio queue → sender task → client frames
```

---

## 5. The Gateway — how services connect

Source: `services/gateway-service/app/main.py`, `app/routing.py`.

### 5.1 Route-ownership table

The gateway matches the normalized public path against ordered regex patterns; **first match wins**:

| # | Owner | Routes matched | Upstream |
|---|---|---|---|
| 1 | platform-organizations | `/api/v1/platform/organizations[/{uuid}[/owners\|memberships\|invitations\|security]]`, `/api/v1/platform/identities/{uuid}/memberships` | organization :8000 |
| 2 | platform-identity | `/api/v1/platform/me\|admins\|audit\|sessions[/{uuid}/revoke]\|identities[/{uuid}[/sessions/revoke]]` | identity :8001 |
| 3 | messaging-conversation | `/api/v1/conversations/{id}/(messages/**\|delivered\|read)` | messaging :8004 |
| 4 | messaging-message | `/api/v1/messages/**` | messaging :8004 |
| 5 | identity-auth | `/api/v1/auth/**` | identity :8001 |
| 6 | identity-user-devices | `/api/v1/users/{uuid}/devices` | identity :8001 |
| 7 | identity-e2ee | `/api/v1/e2ee/**` | identity :8001 |
| 8 | identity-devices | `/api/v1/devices/**` | identity :8001 |
| 9 | contacts | `/api/v1/contacts/**` | user :8002 |
| 10 | user | `/api/v1/users/**` | user :8002 |
| 11 | conversation | `/api/v1/conversations/**` | conversation :8003 |
| 12 | media | `/api/v1/media/**` | media :8005 |
| 13 | notification | `/api/v1/notifications/**` | notification :8006 |
| 14 | organization | `/api/v1/{organizations\|branches\|teams\|members\|invitations\|roles\|permissions\|role-assignments\|audit-logs}/**` | organization :8000 |

Rules encoded here:

- **Messaging beats conversation**: `/conversations/{id}/messages` goes to messaging-service, while all other `/conversations/**` goes to conversation-service (patterns 3 and 4 precede 11).
- **Internal isolation**: `/internal/v1/**` matches no owner → never publicly reachable. Internal endpoints are only callable service-to-service.
- **Unmatched paths** → `404 {"detail": "Not found", "correlation_id": …}` from the gateway itself.

### 5.2 Proxy mechanics (per request)

1. **Health endpoints** — gateway serves its own `/health/live` and `/health/ready`.
2. **Platform service status** — `GET /api/v1/platform/services` requires a platform admin JWT (checks `platform.services.read` permission via identity), then probes live/ready of every upstream and reports `realtime_public_wss_url`.
3. **Rate limiting** — Redis sliding-window limits: stricter bucket for `/api/v1/auth/**` (`RATE_LIMIT_AUTH_PER_MINUTE`), general bucket for the rest (`RATE_LIMIT_API_PER_MINUTE`). Falls back to in-memory store if Redis is unavailable.
4. **Body size guard** — requests larger than `max_request_bytes` → `413`.
5. **Header allowlist** — forwards only: `accept`, `accept-language`, `authorization`, `content-type`, `idempotency-key`, `user-agent`, `x-correlation-id`, `x-request-id`. Injects/generates `x-correlation-id`, sets `x-forwarded-for` and `x-forwarded-proto`.
6. **Retries** — GET/HEAD retried once per `upstream_idempotent_retries` with tiny backoff on timeouts/network errors.
7. **Error mapping** — upstream timeout → `504`, connection error → `502`, each with the correlation ID.
8. **Response header allowlist** — passes back only cache/content/correlation headers; adds security headers via `SecurityHeadersMiddleware` (strict in production).
9. **CORS** — restricted to `CORS_ALLOWED_ORIGINS`, credentials allowed, methods GET/POST/PUT/PATCH/DELETE/OPTIONS.

### 5.3 Service-to-service connectivity

Services reach each other **only** through:

- **Internal HTTP endpoints** (`/internal/v1/**`, never gateway-routed), authenticated with `INTERNAL_SERVICE_TOKEN` / `SERVICE_AUTH_TOKEN` headers. Examples:
  - conversation → messaging/realtime: `POST /internal/v1/conversations/{cid}/authorize` (per-conversation permission check)
  - messaging/media → user: `POST /internal/v1/users/block-check`, `POST /internal/v1/users/projections`
  - organization → identity: `POST /api/internal/v1/identity-memberships/{id}`
  - media: `POST /internal/v1/media/profile-photos/{id}`; user: `POST /internal/v1/users/provision|company-owner`
- **RabbitMQ events** for anything that can be asynchronous (see §10).

---

## 6. Service catalog

| Service | Port | Stack | Database | Workers |
|---|---:|---|---|---|
| organization-service | 8000 | Django 5.2 + DRF, Gunicorn, drf-spectacular, whitenoise | `teamchat_organization_db` | outbox publisher (`manage.py publish_outbox`), invitation expiry |
| identity-service | 8001 | FastAPI, SQLAlchemy 2 async, asyncpg, argon2-cffi, phonenumbers | `teamchat_identity_db`, Redis | outbox runner, consumer runner |
| user-service | 8002 | FastAPI, SQLAlchemy, aio-pika | `teamchat_user_db` | outbox runner, consumer runner |
| conversation-service | 8003 | FastAPI, SQLAlchemy, redis, pika | `teamchat_conversation_db`, Redis | outbox runner, consumer runner |
| messaging-service | 8004 | FastAPI, SQLAlchemy, pika | `teamchat_message_db` | outbox runner, consumer runner |
| media-service | 8005 | FastAPI, SQLAlchemy, boto3 | `teamchat_media_db`, S3/local | outbox runner, consumer runner, cleanup runner |
| notification-service | 8006 | FastAPI, SQLAlchemy, firebase-admin | `teamchat_notification_db` | outbox runner, consumer runner, delivery worker (FCM) |
| realtime-service | 8007 | FastAPI + native WebSocket, redis, pika | — (Redis only) | consumer runner |
| gateway-service | 8008 | FastAPI + httpx proxy, Redis rate limits | — | — |

All FastAPI services run via `uvicorn app.main:app`; every service exposes `/health/live` and `/health/ready`.

---

## 7. Data models per service

### 7.1 identity-service (`app/models/models.py`)

- `Identity` — phone_number, email, password_hash, contact_phone_digest, phone/email_verified, status (`PENDING | ACTIVE | SUSPENDED | DISABLED | DELETED`).
- `Device` — belongs to identity; platform (`ANDROID | IOS | WEB`), installation_id, status.
- `Session` — one active login context = `(organization_id, member_id)` pair; refresh_family_id, expires_at.
- `RefreshCredential` — token_hash per session; family_id + rotation status (reuse detection kills the family).
- `OTPChallenge` — purpose, code_hash, attempt_count, unique `provider_request_id` (Vonage Verify mapping).
- `QRLoginChallenge` — deep-link device pairing.
- `PasswordResetChallenge`, `EmailVerificationChallenge`.
- `PlatformGrant` — super-admin/platform-admin grants; `PlatformAudit`, `SecurityAuditEvent`.
- `MembershipProjection` — org memberships mirrored from organization events.
- `ProcessedEvent` (consumer inbox dedupe), `OutboxEvent`.

### 7.2 organization-service (Django apps)

- `Organization` (+ 1:1 `OrganizationSettings`), multi-tenancy via `Entity`/`TenantEntity` bases.
- `Branch` + `BranchMembership`; `Team` + `TeamMembership`.
- `Member`.
- `Invitation` — token_hash, intended_role, expires_at.
- `Role`, `Permission`, `RolePermission`, `RoleAssignment`.
- `AuditLog`.

### 7.3 conversation-service (`app/models.py`)

- `Conversation` — type (`direct | group`), status.
- `ConversationMember` — membership + role.
- `MemberState` — per-member read/mute state.
- `ConversationSettings`.
- Projections: `ConversationMessageProjection`, `ConversationReadProjection`, `MemberProjection`, `BlockProjection`.

### 7.4 messaging-service (`app/models.py`)

- `Message` — content, author, timestamps, edit/delete markers.
- `ConversationSequence` — per-conversation monotonic sequence numbers.
- `MessageReaction`.
- `ConversationReadState` — delivered/read cursors.
- `PersonalBroadcastList` + `Recipient` — saved recipient lists for personal broadcasts.
- Projections: media, conversation, member.

### 7.5 media-service (`app/models.py`)

- `Media` — upload session + metadata; `MediaReference`.
- `ProfilePhoto`.
- `OrganizationStorageUsage`, `PersonalStorageUsage` — quota tracking.
- `RevokedOrgMember`.

### 7.6 notification-service (`app/models.py`)

- `DevicePushToken` (FCM), `NotificationPreference`, `Notification`, `NotificationDelivery`, `ConversationMute`.
- Projections: user, membership, conversation, block, identity-phone.

---

## 8. Complete API reference

All public routes live under `/api/v1/` behind the gateway. `Authorization: Bearer <access JWT>` required unless noted.

### 8.1 identity-service (:8001) — auth, devices, platform

`app/api/v1/auth.py` — prefix `/api/v1/auth`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/otp/request` | Request OTP challenge (202; dev/SMS/Vonage provider) |
| POST | `/auth/otp/verify` | Verify OTP → tokens |
| POST | `/auth/refresh` | Rotate refresh → new tokens |
| POST | `/auth/logout` | Revoke current session |
| POST | `/auth/logout-all` | Revoke all sessions |
| POST | `/auth/context` | Switch session context (org/member pair) → tokens |
| GET | `/auth/me` | Current identity + membership context |
| POST | `/auth/qr/challenges` | Create QR login challenge (201) |
| GET | `/auth/qr/challenges/{id}/status` | Poll QR pairing status |
| POST | `/auth/qr/challenges/{id}/authorize` | Approve from logged-in device |
| POST | `/auth/qr/challenges/{id}/consume` | Exchange approval → tokens (mobile) |

`app/api/v1/password.py` — prefix `/api/v1/auth`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/login` | Email+password login → tokens |
| POST | `/auth/registration/personal` | Personal account signup (201) |
| POST | `/auth/registration/company` | Company signup by new user (201) |
| POST | `/auth/password/forgot` | Start password reset |
| POST | `/auth/password/reset` | Complete reset (204) |
| POST | `/auth/email/verify` | Verify email (204) |
| POST | `/auth/email/verification/resend` | Resend verification email |
| POST | `/auth/invitations/password` | Set password via invitation → tokens |

`app/api/v1/registration.py` — prefix `/api/v1/auth/registration/company`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/start` | Start company registration challenge (202) |
| POST | `/resend` | Resend verification (202) |
| POST | `/verify` | Verify → tokens |

`app/api/v1/invitations.py` — prefix `/api/v1/auth/invitations`:

| Method | Path | Purpose |
|---|---|---|
| POST | `/validate` | Validate invitation token |
| POST | `/request` | Request invitation challenge (202) |
| POST | `/resend` | Resend challenge (202) |
| POST | `/verify` | Verify → tokens (join) |

`app/api/v1/sessions.py` — prefix `/api/v1/auth/sessions`:

| Method | Path | Purpose |
|---|---|---|
| GET | `` | List own sessions |
| POST | `/{session_id}/revoke` | Revoke one session |

`app/api/v1/devices.py` — prefix `/api/v1/devices`:

| Method | Path | Purpose |
|---|---|---|
| GET | `` | List own devices |
| GET | `/{device_id}` | Device detail |
| POST | `/{device_id}/revoke` | Revoke device + sessions |

`app/api/v1/e2ee.py`:

| Method | Path | Purpose |
|---|---|---|
| PUT | `/api/v1/devices/{device_id}/keys` | Upload device identity keys (204) |
| POST | `/api/v1/devices/{device_id}/prekeys/replenish` | Replenish one-time prekeys |
| GET | `/api/v1/users/{identity_id}/devices` | Fetch public E2EE device bundle for a user |
| GET | `/api/v1/e2ee/…` | Sender-key distribution lookup |

`app/api/v1/platform.py` — prefix `/api/v1/platform` (super-admin only):

| Method | Path | Purpose |
|---|---|---|
| GET | `/platform/me` | Platform operator profile + permissions |
| GET | `/platform/identities` | Search identities |
| GET | `/platform/identities/{id}` | Identity detail |
| GET | `/platform/admins` | List platform admins |
| GET | `/platform/sessions` | All active sessions |
| POST | `/platform/sessions/{id}/revoke` | Force-revoke session |
| POST | `/platform/identities/{id}/sessions/revoke` | Revoke all sessions of identity |
| GET | `/platform/audit` | Security audit trail |

Internal (never gateway-routed): `POST /internal/v1/contact-discovery` — batched phone-digest lookup (HMAC `CONTACT_MATCHING_SECRET`).

### 8.2 organization-service (:8000, Django/DRF) — `config/urls.py`

DRF `DefaultRouter` viewsets under `/api/v1/` (standard list/retrieve/create/update/partial_update/delete per resource):

| Resource | Endpoint base |
|---|---|
| Organizations | `/api/v1/organizations/` |
| Branches | `/api/v1/branches/` |
| Teams | `/api/v1/teams/` |
| Members | `/api/v1/members/` |
| Invitations | `/api/v1/invitations/` |
| Roles | `/api/v1/roles/` |
| Permissions | `/api/v1/permissions/` |
| Role assignments | `/api/v1/role-assignments/` |
| Audit logs | `/api/v1/audit-logs/` |

Platform admin views (super-admin):

- `GET /api/v1/platform/organizations/` (+ `/{org_id}/`, `/owners/`, `/memberships/`, `/invitations/`, `/security/`)
- `GET /api/v1/platform/identities/{identity_id}/memberships/`

Internal (service-to-service):

- `POST /api/internal/v1/invitations/{action}/` (invitation onboarding hooks)
- `POST /api/internal/v1/company-registration/` (company provisioning from identity flow)
- `POST /api/internal/v1/identity-memberships/{identity_id}/`

Ops: `/health/live`, `/health/ready`, `/admin/` (Django operator admin), `/api/schema/` (OpenAPI), `/api/docs/` + `/api/redoc/` (local only). Management commands: `provision_organization`, `expire_invitations`, `organization_lifecycle`, `link_member`.

### 8.3 user-service (:8002)

Public (`app/main.py`, `app/contacts.py`, `app/profile_photos.py`):

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/users/me` | Own profile |
| PATCH | `/api/v1/users/me` | Update profile |
| GET / PATCH | `/api/v1/users/me/preferences` | Notification/appearance prefs |
| GET / PATCH | `/api/v1/users/me/privacy` | Privacy settings |
| GET | `/api/v1/users/me/blocked` | Blocked users |
| POST | `/api/v1/users/{user_id}/block` | Block user |
| DELETE | `/api/v1/users/{user_id}/block` | Unblock user |
| GET | `/api/v1/users/search` | Directory search |
| GET | `/api/v1/users/{user_id}` | Public profile |
| PUT / DELETE | `/api/v1/users/me/photo` | Set/remove profile photo |
| GET | `/api/v1/users/profile-photos/{media_id}` | Fetch profile photo |
| POST | `/api/v1/contacts/match` | Contact discovery via phone digests |
| GET / POST | `/api/v1/contacts` | List / save contacts |
| GET / PATCH / DELETE | `/api/v1/contacts/{contact_id}` | Contact CRUD |

Internal: `POST /internal/v1/users/block-check`, `POST /internal/v1/users/projections`, `POST /internal/v1/users/provision`, `POST /internal/v1/users/company-owner`, `/internal/v1/contacts/**`.

### 8.4 conversation-service (:8003) — `app/api.py`, prefix `/api/v1/conversations`

| Method | Path | Purpose |
|---|---|---|
| POST | `/direct` | Create org-scoped direct conversation (201) |
| POST | `/personal/direct` | Create personal DM (201) |
| POST | `/groups` | Create org group (201) |
| POST | `/personal/groups` | Create personal group (201) |
| GET | `` | List conversations (cursor-paginated) |
| GET | `/{cid}` | Conversation detail |
| PATCH | `/{cid}` | Update name/settings |
| PATCH | `/{cid}/state` | Update own member state (mute/pin/read) |
| POST | `/{cid}/members` | Add members |
| DELETE | `/{cid}/members/{mid}` | Remove member |
| GET | `/{cid}/members` | List members |
| POST | `/{cid}/members/{mid}/promote` | Promote to admin |
| POST | `/{cid}/members/{mid}/demote` | Demote admin |
| POST | `/{cid}/transfer-ownership` | Transfer conversation ownership |
| POST | `/{cid}/leave` | Leave conversation |
| POST | `/{cid}/close` | Close conversation |
| POST | `/{cid}/delete` | Delete conversation |

Internal: `POST /internal/v1/conversations/{cid}/authorize` — the authorization checkpoint messaging and media call before accepting writes.

### 8.5 messaging-service (:8004) — `app/main.py`

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/conversations/{cid}/messages` | Send message (sequence-assigned) |
| GET | `/api/v1/conversations/{cid}/messages` | Paginated history |
| GET | `/api/v1/messages/{id}` | Single message |
| PATCH | `/api/v1/messages/{id}` | Edit own message |
| DELETE | `/api/v1/messages/{id}` | Delete own message |
| POST | `/api/v1/messages/{id}/reactions` | Add reaction |
| DELETE | `/api/v1/messages/{id}/reactions/{reaction}` | Remove reaction |
| POST | `/api/v1/conversations/{cid}/delivered` | Mark delivered cursor |
| POST | `/api/v1/conversations/{cid}/read` | Mark read cursor |
| POST | `/api/v1/personal/broadcast-lists` | Create broadcast list (201) |
| POST | `/api/v1/personal/broadcast-lists/{list_id}/recipients` | Add recipients (201) |
| POST | `/api/v1/personal/broadcast-lists/{list_id}/messages` | Broadcast to list (201) |

### 8.6 media-service (:8005) — `app/main.py`, `app/profile_photos.py`

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/media/uploads` | Create single upload session (201, presigned) |
| POST | `/api/v1/media/{id}/complete` | Finalize single upload |
| POST | `/api/v1/media/multipart` | Start multipart upload (201) |
| POST | `/api/v1/media/{id}/multipart/parts` | Presign part upload |
| GET | `/api/v1/media/{id}/multipart` | List uploaded parts |
| POST | `/api/v1/media/{id}/multipart/complete` | Complete multipart |
| DELETE | `/api/v1/media/{id}/multipart` | Abort multipart |
| GET | `/api/v1/media/{id}/download` | Presigned download |
| DELETE | `/api/v1/media/{id}` | Delete media |
| POST | `/api/v1/media/profile-photos/uploads` | Profile photo upload (201) |
| POST | `/api/v1/media/profile-photos/{photo_id}/complete` | Finalize profile photo |

Local-dev only: `PUT|GET /local-storage/{token}` (direct byte transfer against the filesystem adapter). Internal: `POST /internal/v1/media/profile-photos/{photo_id}`.

Bytes never flow through the gateway — clients upload/download directly to S3 (prod) or the media service's local endpoints (dev).

### 8.7 notification-service (:8006) — `app/main.py`

| Method | Path | Purpose |
|---|---|---|
| PUT | `/api/v1/notifications/devices/current/token` | Register FCM push token |
| DELETE | `/api/v1/notifications/devices/current/token` | Remove push token |
| GET / PATCH | `/api/v1/notifications/preferences` | Notification preferences |
| PUT | `/api/v1/notifications/conversations/{cid}/mute` | Mute conversation |
| DELETE | `/api/v1/notifications/conversations/{cid}/mute` | Unmute conversation |
| GET | `/api/v1/notifications` | List notifications (paginated) |
| GET | `/api/v1/notifications/unread-count` | Unread badge count |
| POST | `/api/v1/notifications/{id}/read` | Mark read |
| POST | `/api/v1/notifications/read-all` | Mark all read |

### 8.8 realtime-service (:8007)

`WS /api/v1/realtime?token=<access JWT>` — see §9. Plus `/health/live`, `/health/ready`.

---

## 9. Realtime WebSocket protocol

Raw WebSocket (no Socket.IO) at realtime-service :8007, authenticated by access JWT query param.

### 9.1 Client → server frames (JSON, `version: 1`)

| Frame | Purpose |
|---|---|
| `ping` | Liveness |
| `subscribe` / `unsubscribe` | Join/leave conversation event streams |
| `typing.start` / `typing.stop` | Typing indicators |
| `presence.heartbeat` | Keep presence alive (~30 s) |
| `presence.subscribe` | Watch other users' presence |
| `e2ee.sender_key_distribution` | Distribute sender keys for E2EE groups |

### 9.2 Server → client events (versioned)

`connection.ready.v1`, `connection.resync_required.v1`, `message.created.v1`, `message.edited.v1`, `message.deleted.v1`, `message.reaction_added.v1`, `message.reaction_removed.v1`, `message.delivered.v1`, `message.read.v1`, `conversation.*` (created/updated/member changes), `typing.updated.v1`, `presence.updated.v1`, `presence.snapshot`, `realtime.delivery.v1`, `workspace.revoked.v1`.

### 9.3 Fanout internals

`app/events.py` `EventConsumer` consumes RabbitMQ, dedupes via `ProcessedEvent`, consults the per-instance Redis subscription registry (`app/registry.py`, keys TTL 90 s), fans out across instances, and delivers through per-connection asyncio queues to a sender task. Multiple realtime instances scale horizontally behind `ws.michat.in`.

---

## 10. Event pipeline

### 10.1 Exchanges

Topic exchanges: `organization.events` (dominant — carries org, conversation, and identity events too), `user.events`, `messaging.events`, `media.events`, `notification.events`. Dead-lettering: `organization.dead` → `organization.events.dead`, with an archive queue `organization.events.archive`. Contract envelope: `services/organization-service/events/schemas/envelope.v1.json`; matrix in `docs/platform/EVENT_CONTRACT_MATRIX.md`.

### 10.2 Lifecycle of one message send

1. `POST /conversations/{cid}/messages` → gateway → messaging-service.
2. Messaging calls conversation-service `POST /internal/v1/conversations/{cid}/authorize` (membership/permission check, block list via user-service internal API).
3. Transaction: insert `Message`, bump `ConversationSequence`, insert `Message` outbox event, update read state.
4. Outbox publisher → RabbitMQ `organization.events`.
5. Consumers: conversation (message projection → list ordering), notification (fanout + FCM push, respecting mutes/preferences), realtime (`message.created.v1` → subscribed sockets), media/user projections where relevant.
6. Recipients' clients receive the WS frame and reconcile.

---

## 11. Authentication & security

- **Access tokens**: JWT **RS256**, ~15 min TTL, issued only by identity-service (`app/security/tokens.py`). Claims include `org` + `mid` (must be a valid pair). All services verify with the shared `JWT_PUBLIC_KEY` / `IDENTITY_JWT_PUBLIC_KEY` — no token introspection on hot paths.
- **Refresh tokens**: opaque, stored hashed (`RefreshCredential`), rotated within a `refresh_family_id`; reuse of a rotated token revokes the family.
- **Password hashing**: Argon2 (`argon2-cffi`).
- **OTP**: pluggable `app/integrations/otp_provider.py` — `DevelopmentOTPProvider`, `HiliteSMSOTPProvider`, `VonageVerifyOTPProvider` (`/verify/json` + `/verify/check/json`; `provider_request_id` persisted). Phone OTP disabled by default (`403 PHONE_OTP_DISABLED`) — email/password is the primary path.
- **Service auth**: `INTERNAL_SERVICE_TOKEN` / `SERVICE_AUTH_TOKEN` headers on `/internal/v1/**`; per-conversation authorization delegated to conversation-service.
- **Gateway hardening**: Redis rate limits (auth vs general buckets), request-size cap, header allowlists both directions, security headers, CORS allowlist, correlation IDs end-to-end.
- **Platform admin**: separate `PlatformGrant` + `platform.*` permissions; operator Django admin at `/admin/` is a separate login from product auth.
- **Local dev keys**: `services/identity-service/.local-keys` via `generate_local_keys.py`/`.ps1`.
- **Dev-only hazard**: the `X-Dev-Member-ID` adapter is deliberately unsafe and must never be exposed publicly.

---

## 12. External integrations

| Integration | Used by | Purpose |
|---|---|---|
| Vonage Verify | identity | Phone OTP (current production rollout) |
| HiliteSMS | identity | Alternative SMS OTP gateway |
| Firebase Cloud Messaging | notification | Mobile/web push delivery |
| SMTP | identity/organization | Email verification, password reset, invitation emails |
| AWS S3 | media | Presigned upload/download/multipart (`MEDIA_S3_BUCKET`, `MEDIA_STORAGE_BACKEND` switches to local filesystem in dev) |

---

## 13. Frontend system

### 13.1 Apps

| App | Stack | Role |
|---|---|---|
| `apps/web/web-chat-app` | Next.js 16.3 + React 19.2 + TS, App Router | End-user chat + workspace |
| `apps/admin-web/admin-webchat-app` | Same | Platform admin console |
| `apps/mobile/globalchatapp` | Flutter (Riverpod, go_router, Dio, Firebase, libsignal) | Mobile chat with E2EE + QR pairing |

Boundary: admin console is platform-only; web app is workspace + chat (docs/local-development/frontend/FRONTEND-ARCHITECTURE.md).

### 13.2 Web app structure

- **Entry**: `app/page.tsx` → `components/globalchat-app.tsx` → `Login` or desktop shell. Chat shell = client-side section switching (app rail → list pane → main pane; mobile bottom nav). Routes exist for auth (`/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/join`) and workspace sections (`/workspace/{overview,members,teams,branches,invitations,roles,settings,company,devices,profile}`, `/contacts`).
- **Admin routes**: `(admin)/{dashboard,organizations,users,platform-admins,sessions,roles,audit-logs,system,settings,invitations,members,branches,teams,devices,conversations,notifications,profile,security}`.
- **Chat features**: conversation list, thread + composer (pagination, forward, copy, receipts, typing), conversation details/sidebar, new-chat/team pickers, media (attachments, voice recorder, viewer), notifications, settings, generic workspace admin resource screens.
- **State**: React Context + hooks — `AuthProvider` (session, permissions Set, profile), `use-chat-controller` (conversations, socket, reconnect), `use-contacts`, `use-notifications`. Cross-tree signals via window CustomEvents (`globalchat:session-expired`, `globalchat:admin-refresh`, `globalchat:profile-updated`).
- **API access**: same-origin Next.js proxy `app/api/gateway/[...path]/route.ts` → `NEXT_PUBLIC_API_URL`, restricted to `/api/v1/*`. Fetch wrapper `workspace/lib/api/client.ts` implements single-flight refresh-token rotation.
- **Realtime**: `lib/websocket/connection.ts` → `wss://ws.michat.in/api/v1/realtime?token=…`; subscribe/typing/heartbeat frames; 15 s reconciliation reloads on inbound events; exponential backoff reconnect (max 30 s).
- **Styling**: Tailwind CSS v4 (CSS-first `@theme`) + Aurora design system (`--aurora-*` tokens, primary `#635BFF`, light/dark in `localStorage globalchat.theme`); lucide-react icons; sonner toasts.
- **Token storage**: `localStorage globalchat.session` (web), `sessionStorage globalchat.admin.session` (admin); guards via `admin-guard.tsx` + workspace permission filters.

### 13.3 Frozen web-chat phases (commit `7079fc4`)

1. Personal accounts foundation
2. Contact discovery (phone-digest matching)
3. Personal chats + tenant-independent conversation/messaging/realtime/media authorization
4. Company creation by existing users
5. Owner/admin-only group creation restriction
6. Production invitation email + notification/settings gates (read-only inbox, browser-permission push, frontend-local appearance)

---

## 14. Configuration

Root `.env.example` (copy to `.env`; production template `deploy/hostinger/.env.example`). Key groups:

- **Datastores**: `DATABASE_URL` (postgresql+asyncpg), `REDIS_URL`, `RABBITMQ_URL`, `RABBITMQ_EXCHANGE`, `RABBITMQ_PREFETCH_COUNT`
- **JWT**: `ACCESS_TOKEN_PRIVATE_KEY/PUBLIC_KEY/KID/TTL`, `REFRESH_TOKEN_TTL`, `JWT_PUBLIC_KEY`, `IDENTITY_JWT_*` (algorithm/issuer)
- **OTP/SMS**: `OTP_PROVIDER`, `OTP_TTL`, `OTP_MAX_ATTEMPTS`, `OTP_RESEND_COOLDOWN`, `VONAGE_API_KEY/SECRET/BRAND/VERIFY_BASE_URL/TIMEOUT`, 7× `SMS_*`
- **Login extras**: `QR_CHALLENGE_TTL`, `QR_DEEP_LINK_BASE`
- **Policy**: `REGISTRATION_POLICY=INVITE_ONLY`, `RATE_LIMIT_*`, `CONTACT_MATCHING_SECRET`
- **Service mesh**: `INTERNAL_SERVICE_TOKEN`, `SERVICE_AUTH_TOKEN`, cross-service URLs, `TRUSTED_PROXY_CIDRS`, `CORS_ALLOWED_ORIGINS`, `ALLOWED_HOSTS`
- **Push/media**: `FIREBASE_CREDENTIALS_JSON`, `PUSH_PROVIDER`, `MEDIA_S3_BUCKET`, `AWS_REGION`, `MEDIA_JWT_SECRET`
- **Outbox tuning**: `OUTBOX_BATCH_SIZE`, `OUTBOX_POLL_SECONDS`, `OUTBOX_MAX_RETRIES`, `DATABASE_POOL_SIZE`, `MAX_OVERFLOW`

---

## 15. Deployment

- **Production (current)**: `deploy/hostinger/` — Docker Compose with Postgres 16, Caddy TLS termination (`api.michat.in` → gateway :8008; `ws.michat.in` → realtime :8007), one API container + separate outbox/consumer/delivery containers per service, `scripts/migrate-all.sh`. AWS is decommissioned (`docs/operations/AWS-PRODUCTION-DECOMMISSIONED.md`); `infrastructure/aws/s3-media` remains for S3 media policy reference.
- **Local**: root `docker-compose.yml` (redis, rabbitmq, org + outbox, identity + outbox, notification api/consumer, realtime api/consumer, user, conversation, messaging, media).

---

## 16. Testing

- **Backend**: per-service `tests/` under pytest — identity 26 files, messaging/realtime/user 18 each, notification 17, organization 12 (pytest-django, `config.settings.test`), conversation/media 11 each, gateway 4. Async services use SQLite (`aiosqlite`) for unit tests; `integration` marker opts into live RabbitMQ/Postgres. Cross-service contract suite: `tests/cross_service/test_event_contracts.py`.
- **Web/admin**: Vitest + Testing Library + jsdom (21 test files in web; api-client/auth/login/company-registration/invitations/owner-panel/resource-screen in admin), Playwright live scripts (`npm run test:live`).
- **Manual test guides**: `docs/local-development/manual-testing/01`–`14` covering health, registration, auth, profile, org, branches/teams, invitations, conversations, messaging, media, notifications, realtime, devices/sessions, end-to-end.

---

## 17. Local development

```powershell
Copy-Item .env.example .env     # replace placeholder secrets
docker compose up -d --build
docker compose exec organization-service python manage.py provision_organization `
  --name "Example" --slug example --owner-name "Owner" `
  --owner-user-id "11111111-1111-4111-8111-111111111111"
```

- Managed runner: `python scripts/local/dev.py` (start services + workers, migrate, seed, smoke).
- Swagger: http://localhost:8000/api/docs/ • Django admin: http://localhost:8000/admin/
- Gateway: http://localhost:8008 • Realtime WS: ws://127.0.0.1:8007/api/v1/realtime
- Docs index: `docs/local-development/01-LOCAL-SETUP.md`, `02-DOCKER-INFRASTRUCTURE.md`, `03-DATABASES.md`, `04-AUTHENTICATION.md`.

---

## 18. Known gaps

- `packages/` (api-contracts, event-contracts, observability) are empty scaffolds — event contracts actually live in `services/organization-service/events/schemas/`.
- `docs/{api,architecture,database,events}/` are placeholder folders.
- Phone OTP disabled by default; E2EE endpoints exist but the web client relies on transport security (mobile uses libsignal).
- Dev `X-Dev-Member-ID` adapter must never be exposed publicly.
- Admin known-gaps ledger: `docs/local-development/admin/KNOWN-GAPS.md`.
