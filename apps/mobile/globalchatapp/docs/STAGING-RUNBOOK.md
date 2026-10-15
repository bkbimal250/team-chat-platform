# GlobalChat mobile — staging runbook

Use this to stand up a **staging** stack and point the Flutter client at it. No secrets in this doc — inject credentials via your secret manager or local `.env` files (never commit).

## Contract verification (code-aligned)

Verified against repository sources on 2026-10-14.

| Area | Requirement | Source of truth |
|------|-------------|-----------------|
| **Gateway HTTP** | Single public REST origin; proxies to downstream services | `services/gateway-service/app/routing.py`, `ROUTE_AUDIT.md` |
| **Realtime WSS** | **Not** proxied by gateway; dedicated origin + path `/api/v1/realtime` | `gateway-service/OPERATIONS.md`, `AppConfig.realtimeWssUrl` |
| **Identity E2EE** | `PUT /api/v1/devices/{id}/keys`, `POST .../prekeys/replenish`, `GET /api/v1/users/{identity}/devices`, `GET /api/v1/e2ee/prekey-bundle/{identity}/{device}` | `identity-service/app/api/v1/e2ee.py`, mobile `e2ee_api.dart` |
| **Auth context** | `POST /api/v1/auth/context` with `organization_id` (workspace switch) | `identity-service/app/api/v1/auth.py`, mobile `auth_api.dart` |
| **Messaging E2EE** | `type: E2EE` + JSON `e2ee` envelope; column `messages.e2ee_envelope` | `messaging-service` migration `0005_message_e2ee_envelope.py`, `schemas.py` |
| **Org members** | `GET /api/v1/members/` (paginated `results`) for workspace group picker | `organization-service` `MemberViewSet`, mobile `members_api.dart` |
| **Media** | `POST /api/v1/media/uploads` → PUT presigned URL → **`POST /api/v1/media/{id}/complete`** → `GET .../download` | `media-service/app/main.py`, mobile `media_api.dart` |
| **WSS server → client** | `message.created/edited/deleted.v1`, `message.reaction_*`, `message.delivered/read.v1`, `typing.updated.v1`, `connection.resync_required.v1`, `e2ee.sender_key_distribution.v1` | `realtime-service/app/events.py`, `e2ee_distribution.py`, mobile `chat_controller.dart` |
| **WSS client → server** | `subscribe` / `unsubscribe`, `typing.start` / `typing.stop`, `e2ee.sender_key_distribution` | `realtime-service/app/main.py`, mobile `realtime_client.dart` |

### Migrations that must be applied before mobile E2EE/media

| Service | Tool | Blocking revision / note |
|---------|------|---------------------------|
| identity-service | Alembic | `0011_device_e2ee_keys` (`device_e2ee_bundles`, `device_one_time_prekeys`) |
| messaging-service | Alembic | `0005_message_e2ee_envelope` (`messages.e2ee_envelope`) |
| conversation-service | Alembic | Personal/group routes used by mobile (`0003_personal_direct`, `0004_personal_groups` if not already head) |
| media-service | Alembic | `0001_media_schema` + later (durable uploads) |
| organization-service | Django `migrate` | Members API and tenant scoping |
| user-service | Alembic | Contacts (`0003_contacts`) for personal group picker |

Realtime and gateway do not own app databases; they must reach Redis/RabbitMQ and downstream URLs configured in gateway.

## Environment variables

### Staging platform (operators)

Set per service from each `services/*-service/.env.example` and `gateway-service/.env.example`. Typical groups:

| Variable family | Used by | Purpose |
|-----------------|---------|---------|
| `DATABASE_URL` | identity, messaging, conversation, media, user, notification | Postgres per service DB |
| `RABBITMQ_URL` | services with outbox/consumers | Events → realtime, notifications, projections |
| `REDIS_URL` | realtime, rate limits, caches | Realtime registry / delivery |
| `JWT_PUBLIC_KEY` / signing keys | all authenticated APIs | Bearer validation |
| `INTERNAL_SERVICE_TOKEN` | internal service calls | Not for mobile clients |
| `IDENTITY_URL`, `MESSAGING_URL`, … | gateway | Upstream routing (`gateway-service/app/config.py`) |
| `REALTIME_URL` | gateway (health/metadata) | Internal realtime HTTP |
| `REALTIME_PUBLIC_WSS_URL` | gateway `GET /api/v1/platform/services` | **Advertised** WSS URL for clients |
| Media storage (`MEDIA_*`, S3 or local) | media-service | Presigned upload/download |

### Flutter client (`--dart-define`)

| Define | Staging example | Default in app |
|--------|-----------------|----------------|
| `API_BASE_URL` | `https://api.staging.example.com` | `https://api.michat.in` |
| `REALTIME_WSS_URL` | `wss://ws.staging.example.com/api/v1/realtime` | `wss://ws.michat.in/api/v1/realtime` |

Android emulator to **local** stack (from `README.md`):

```text
API_BASE_URL=http://10.0.2.2:8008
REALTIME_WSS_URL=ws://10.0.2.2:8007/api/v1/realtime
```

## Startup order (logical)

1. **Postgres, Redis, RabbitMQ** (and object storage for media if not using local disk).
2. **Migrations** on all owning services (see table above).
3. **Core APIs** (any order once DB is ready): organization → identity → user → conversation → messaging → media → notification.
4. **Workers** (outbox + consumers) for organization, identity, user, conversation, messaging, media, notification, **realtime consumer**.
5. **Realtime** HTTP/WSS service (port 8007 in local layout).
6. **Gateway** last (port 8008 local) — depends on upstream URLs.

### VPS staging / production-like

Use `deploy/hostinger/README.md` on a Hostinger (or any Linux) VPS with Docker Compose, Caddy TLS, and S3 media credentials in `.env`.

### Local Windows reference (developer workstation)

From repo root, after `python scripts/local/dev.py prepare` and `infra`:

```text
python scripts/local/dev.py migrate
python scripts/local/dev.py start
```

Service ports: organization `8000` … gateway `8008`, realtime `8007`.

## Health checks

| Check | Command / URL | Expect |
|-------|---------------|--------|
| Gateway live | `GET {API_BASE_URL}/health/live` | 200 |
| Gateway ready | `GET {API_BASE_URL}/health/ready` | 200, `"status":"ready"` |
| Realtime ready | `GET {REALTIME_HTTP}/health/ready` (often `:8007` on host, not via gateway) | 200 |
| Downstream matrix | `GET {API_BASE_URL}/api/v1/platform/services` with **admin** bearer | Each service `live`/`ready`; includes `realtime_public_wss_url` |
| Identity E2EE | After login + device setup: `GET {API_BASE_URL}/api/v1/auth/me` | `device_id` present |
| Pre-key bundle | `GET {API_BASE_URL}/api/v1/e2ee/prekey-bundle/{identity}/{device}` | 200 JSON bundle |

## Mobile smoke after stack is up

```bash
cd apps/mobile/globalchatapp
flutter pub get
flutter analyze lib
flutter run --dart-define=API_BASE_URL=... --dart-define=REALTIME_WSS_URL=...
```

Complete **device setup** in-app before sending E2EE messages.

## Known staging gaps (not code bugs)

| Gap | Impact |
|-----|--------|
| Mobile org switcher only lists **current** org from `/auth/me` | Switching org in UI requires knowing `organization_id` (e.g. from invitation/admin); listing all memberships needs a future client call to a platform memberships API or operator-supplied IDs |
| Personal workspace | Personal chats use a **personal JWT** (`organization_id` null); `POST /auth/context` is for workspace orgs only |
| Media | Staging must provide working presigned storage; uploads stay `application/octet-stream` ciphertext |
| Push (Firebase) | Optional for messaging validation; not required for E2EE/realtime checklist |

See `STAGING-E2E-CHECKLIST.md` for manual validation steps.
