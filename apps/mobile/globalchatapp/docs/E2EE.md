# End-to-end encryption (mobile)

GlobalChat treats **message content** as client-only plaintext. The backend stores routing metadata and **ciphertext**; operators with database access cannot read bodies or attachment bytes without device keys.

## Data flow

```
Mobile composer
  → encrypt locally (Signal Protocol / libsignal)
Ciphertext envelope
  → HTTPS gateway (messaging API)
Messaging / realtime fan-out
  → recipient devices
Recipient mobile
  → decrypt locally
```

Organization membership controls **who can be in a conversation**, not **who can decrypt**. Cryptographic identity is always the user **identity id** plus **device id** (1–127 per user). Never use `organizationId` as a Signal address name.

## Conversation kinds

| Kind | Encryption |
|------|------------|
| Personal direct | 1:1 Double Ratchet per recipient **device** |
| Workspace direct | Same; workspace is ACL only |
| Personal group | Sender-key (`GroupCipher`) per group `distributionId` |
| Workspace group | Same sender-key model |

## Trust and key changes

`E2eeTrustGuard` blocks new sessions when a remote identity key changes unless the contact was explicitly verified on this device. Decrypt failures surface as in-chat warnings (no silent trust). Users can verify after reviewing fingerprints from `GET /api/v1/users/{id}/devices`.

## Multi-device

Each physical installation calls `DeviceIdentityService.openOrCreateDevice` with its server-issued `deviceId`. A sender encrypts (or distributes sender keys) **per recipient device**. Adding a device generates **new** keys; keys are not cloned from another device.

## Media

See `AttachmentCryptoService`: random per-file AES-256-GCM-SIV key, encrypt before upload, pass **wrapped** key material inside the message ciphertext. S3/gateway never sees the raw file key.

## Code layout

```
lib/security/e2ee/
  models/          wire + domain types
  protocol/        libsignal adapter
  storage/         flutter_secure_storage backed stores
  services/        device, sessions, groups, attachments, trust
  repositories/    backend DTO contracts (no HTTP yet)
```

Initialize via `E2eeFoundation.ensureInitialized()` (called from `bootstrap.dart`).

## Related docs

- `E2EE-BACKEND-CONTRACT.md` — REST shapes for keys and ciphertext
- `KEY-MANAGEMENT.md` — rotation, verification, wipe
