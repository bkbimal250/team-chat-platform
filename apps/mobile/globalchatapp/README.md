# GlobalChat Mobile

Flutter client for **GlobalChat** — one permanent account for personal messaging, workspace messaging, and multiple organizations.

## Stack

- Flutter 3.13+
- Riverpod (state)
- go_router (navigation)
- Dio (gateway / Identity API)
- libsignal (E2EE, Phase 2A+)
- WebSocket realtime client (`REALTIME_WSS_URL`, encrypted sender-key fan-out)
- Firebase Messaging (push bootstrap)

## Setup

```bash
cd apps/mobile/globalchatapp
flutter pub get
```

### Environment (`--dart-define`)

| Variable | Purpose | Default |
|---|---|---|
| `API_BASE_URL` | Gateway HTTPS | `https://api.michat.in` |
| `REALTIME_WSS_URL` | Realtime WebSocket | `wss://ws.michat.in/api/v1/realtime` |

Example:

```bash
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8008 \
  --dart-define=REALTIME_WSS_URL=ws://10.0.2.2:8007/api/v1/realtime
```

## Staging validation

- [STAGING-RUNBOOK.md](docs/STAGING-RUNBOOK.md) — env vars, startup order, migrations, health checks
- [STAGING-E2E-CHECKLIST.md](docs/STAGING-E2E-CHECKLIST.md) — manual E2E sign-off

## Run

```bash
flutter run          # device / emulator
flutter run -d ios
flutter run -d android
```

## Docs

See [`docs/`](docs/) for architecture, navigation, design system, and API integration notes.

## Project layout (high level)

- `lib/app/` — app shell, router
- `lib/theme/` — design tokens & themes
- `lib/components/` — shared UI
- `lib/features/` — feature modules (auth, chats, workspace, …)
- `lib/services/` — API, realtime, storage (expanded in later phases)
- `lib/config/` — runtime configuration
