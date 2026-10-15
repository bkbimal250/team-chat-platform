# API integration

```
Mobile (Dio) → API_BASE_URL (public gateway) → Identity / other services
```

## Configuration

| Define | Purpose |
|--------|---------|
| `API_BASE_URL` | Gateway HTTPS origin (default `https://api.michat.in`) |
| `REALTIME_WSS_URL` | Authenticated WebSocket (`/api/v1/realtime`) |

Example:

```bash
flutter run --dart-define=API_BASE_URL=https://api.example.com
```

## Client layout

```
lib/services/api/
  client/gateway_client.dart   # Dio, timeouts
  interceptors/                # correlation id, bearer auth, errors
  auth/auth_api.dart           # Identity auth routes
  devices/devices_api.dart     # Device list
  models/                      # DTOs
lib/services/auth/
  session_storage.dart         # tokens in flutter_secure_storage
  auth_repository.dart
```

## Rules

- Bearer `Authorization` only — never `X-Organization-ID` or internal service tokens.
- Organization context comes from the session/JWT after login (`organization_id` may be `null` for personal accounts).
- `Idempotency-Key` on login/register/OTP verify mutations.
- `X-Correlation-ID` on every request.
- Do not log tokens, passwords, or key material.

## Identity routes used (Phase 2B)

| Method | Path |
|--------|------|
| POST | `/api/v1/auth/login` |
| POST | `/api/v1/auth/registration/personal` |
| POST | `/api/v1/auth/otp/request` |
| POST | `/api/v1/auth/otp/verify` |
| POST | `/api/v1/auth/password/forgot` |
| POST | `/api/v1/auth/password/reset` |
| POST | `/api/v1/auth/refresh` |
| POST | `/api/v1/auth/logout` |
| GET | `/api/v1/auth/me` |
| GET | `/api/v1/devices` |
| POST | `/api/v1/auth/context` | Switch workspace org (`organization_id`); returns new tokens. Personal chats use a personal session JWT (`organization_id` null), not a separate “personal context” route. |
| GET | `/api/v1/members/` | Workspace member directory (group picker, admin-style lists) |
| POST | `/api/v1/media/uploads` | Initiate encrypted upload (`filename`, `mime_type`, `size_bytes`, `conversation_id`, `media_type`) → `media_id`, `upload_url` |
| POST | `/api/v1/media/{id}/complete` | Finalize upload after PUT to presigned URL (required before `READY` / download) |
| GET | `/api/v1/media/{id}/download` | Presigned `download_url` for ciphertext bytes |

| POST | `/api/v1/conversations/{id}/messages` (`type: E2EE`, `e2ee` envelope) |
| GET | `/api/v1/conversations/{id}/messages` |
| PATCH/DELETE | `/api/v1/messages/{id}` |
| POST | `/api/v1/conversations/{id}/read` / `delivered` |
| PUT | `/api/v1/devices/{id}/keys` |
| GET | `/api/v1/e2ee/prekey-bundle/{identity}/{device}` |

See `E2EE.md` and `E2EE-BACKEND-CONTRACT.md`.
