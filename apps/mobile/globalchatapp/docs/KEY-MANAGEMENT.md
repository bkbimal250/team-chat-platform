# Key management (mobile)

## What lives on device

| Material | Storage |
|----------|---------|
| Identity key pair | `flutter_secure_storage` via `PersistentIdentityKeyStore` |
| Pre-keys, sessions, sender keys | Secure blob store (`gc_e2ee/v1/...`) |
| Explicit verification flags | Secure storage per remote `(identity, device)` |

Never place private keys, session state, plaintext messages, or file keys in SharedPreferences, logs, analytics, or Git.

## Bootstrap (per device)

1. `E2eeFoundation.ensureInitialized()` — load libsignal native library.
2. After auth provides `identityId` + `deviceId`, `DeviceIdentityService.openOrCreateDevice`.
3. `DeviceCryptoBootstrap` → local pre-keys + `E2eeKeysRepository.publishDeviceBundle` (blocked until gateway E2EE routes exist).

Logout clears **auth tokens only**; Signal private keys remain unless the device is revoked and `DeviceCryptoWipe` is invoked.

New device = new `IdentityKeyPair.generate()`; never import another device's private keys.

## Trust & safety numbers

- `DirectSessionService.safetyNumber` — compare with contact out-of-band.
- `IdentityTrustService.markVerified` — user confirmed safety number.
- `PersistentIdentityKeyStore.isTrustedIdentity` — rejects changed keys on **send**; receive uses cautious TOFU until verified.
- Unexpected identity replacement must **not** be auto-trusted; show key-change UI (Phase 2B).

## Rotation

- **Signed pre-key / Kyber**: periodic rotation via new `ensurePreKeys` upload.
- **One-time pre-keys**: replenish when pool < threshold (server signals or local count).
- **Session reset**: delete session record + re-fetch pre-key bundle after device revoke.

## Logout / device removal

`DeviceCryptoWipe.wipeDevice(identityId, deviceId)` deletes all `gc_e2ee/v1/device/...` keys.

## Future

- Encrypted backups: separate backup key hierarchy (not implemented in 2A).
- Calls: SRTP keys derived from Signal sessions (not implemented in 2A).
