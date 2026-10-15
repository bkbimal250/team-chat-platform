# E2EE backend contract (Phase 2B target)

**Status:** Implemented on Identity Service (migration `0011_device_e2ee_keys`). Gateway routes `/api/v1/devices/*/keys`, `/api/v1/e2ee/*`, and `/api/v1/users/{id}/devices` to Identity.

The server holds **public** key material and **ciphertext**. It must not persist plaintext message bodies, session secrets, or attachment encryption keys.

## Identity addressing

- `identityId` — stable user identity (UUID), same as auth identity.
- `deviceId` — integer 1–127, unique per identity.
- Protocol address = `(identityId, deviceId)`.

## Endpoints

### Register / rotate device keys

`PUT /v1/identities/{identityId}/devices/{deviceId}/keys`

Body: `UploadDeviceKeysRequest` (see `lib/security/e2ee/repositories/e2ee_backend_contracts.dart`).

- Stores identity public key, signed pre-key, Kyber pre-key, and batch of one-time pre-keys.
- Re-upload when signed/Kyber keys rotate or one-time pool is low.

### Fetch pre-key bundle (session setup)

`GET /v1/identities/{identityId}/devices/{deviceId}/prekey-bundle`

Returns `PreKeyBundleResponse`. Consumes one one-time pre-key atomically.

### List devices

`GET /v1/identities/{identityId}/devices`

Returns `DeviceListEntry[]` for multi-device fan-out and verification UI.

### Device lifecycle

- `POST /v1/identities/{identityId}/devices` — register new device (returns `deviceId`).
- `DELETE /v1/identities/{identityId}/devices/{deviceId}` — revoke; clients must wipe local keys and peers must reset sessions.

### Messaging (ciphertext only)

`POST /v1/conversations/{conversationId}/messages`

- `content` field is **omitted** or fixed placeholder; real payload in `e2ee` object:
  - `messageType` — libsignal ciphertext type (2/3/7…)
  - `ciphertext` — base64 bytes
  - `recipientDeviceIds` — for sender bookkeeping / sealed routing
- Attachments: `objectKey` + `encryptedAttachment` metadata (nonce, wrapped key, length). Object store holds encrypted blob only.

### Realtime

Events carry the same ciphertext envelope as REST; no plaintext in Rabbit payloads.

## Key change notifications

When identity or signed pre-key changes, emit `device.keys_updated.v1` so clients refresh bundles and may show safety-number / key-change UI.
