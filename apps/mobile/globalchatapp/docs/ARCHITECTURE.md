# Architecture

## Principles

- One **identity**; personal and workspace contexts are scopes, not separate accounts.
- **Server state** (conversations, messages, orgs) stays in feature repositories + Riverpod async providers.
- **UI state** (drafts, selection, theme) stays local or in small notifiers.
- Mobile talks only to the **public gateway** (HTTPS) and **realtime WSS** — never internal service URLs.

## Layers

```
UI (screens / components)
  → feature hooks & controllers
    → repositories / API clients
      → gateway & WSS
```

Phase 1 establishes navigation shell, theme, and empty feature foundations. API wiring lands in Phase 2+.

## End-to-end encryption (Phase 2A)

Cryptography is isolated under `lib/security/e2ee/` and uses **libsignal** (Signal Protocol: X3DH/PQXDH, Double Ratchet, sender-key groups). UI and repositories must call `services/` facades, not libsignal types directly.

```
features (chat, media)
  → security/e2ee/services
    → protocol/libsignal_e2ee_protocol
      → storage (flutter_secure_storage)
```

`bootstrap.dart` initializes `E2eeFoundation` only; per-user device keys are created after authentication. See `docs/E2EE.md`.

## Auth → device → conversations (Phase 2B+)

```
Login (Identity API)
  → DeviceCryptoBootstrap (local libsignal + PUT device keys)
  → Conversations API (personal scope when session has no org)
```

Repositories live under `lib/services/api/` and `lib/features/*/data/`; UI uses Riverpod controllers only.
