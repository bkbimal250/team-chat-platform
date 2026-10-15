# E2EE HTTP API (Identity Service)

Public key material only. All routes require Bearer authentication unless noted.

| Method | Path | Actor |
|--------|------|--------|
| PUT | `/api/v1/devices/{device_id}/keys` | Current device only |
| POST | `/api/v1/devices/{device_id}/prekeys/replenish` | Current device only |
| GET | `/api/v1/users/{identity_id}/devices` | Any authenticated user |
| GET | `/api/v1/e2ee/prekey-bundle/{identity_id}/{device_id}` | Any authenticated user |

`PUT` body: `registration_id`, base64 `identity_key`, `signed_pre_key`, `kyber_pre_key`, optional `one_time_pre_keys[]`.

Bundle fetch atomically consumes one one-time pre-key when available.

Revoking a device deletes its E2EE rows.

Gateway routes `/api/v1/users/{uuid}/devices` and `/api/v1/e2ee/*` to Identity (see gateway `routing.py`).
