# Primary authentication folders

Use `01 - Company Registration` for email/password registration and `02 - Authentication` for login, refresh, logout and invitation password setup. `Phone OTP - Future / Disabled` and preserved phone onboarding folders require explicit feature enablement and must not be run in the current no-SMS flow. Keep password/token variables blank in exported environments.

# Postman testing guide

Source verified: 2026-10-05. Import the collection and environment from `../postman/`. Follow [the fourteen ordered chapters](../manual-testing/README.md), using [service references](../services/README.md) for exact body constraints, responses, permissions and errors. Schema templates contain placeholders; replace them with actual local fixture IDs. Do not run the whole collection automatically: it contains OTP, revocation and destructive requests.

Public business requests use Gateway port 8008. Health/schema, internal operator and signed-storage requests use their actual direct service or returned capability URL. Internal routes are not browser endpoints. WebSocket frames require a separate Postman WebSocket tab. Gateway forwarding is a routing contract, not an additional business endpoint.

Keep Owner and Employee environments separate. Token, OTP and challenge variables are private: never export populated environments. Inspect active OTP_PROVIDER before requesting a code. Development mode alone does not prove that SMS is disabled. Retain rate limits and honor retry_after; never repeat OTP requests automatically.

The existing Company registration and MEMBER INVITATION folders are preserved. Their specialized guides live under `../onboarding/`; admin permissions are documented under `../admin/`.

## Complete operation inventory

| Service | Method | Actual path | Authentication |
|---|---|---|---|
| organization | GET | `/api/v1/audit-logs/` | Bearer access token |
| organization | GET | `/api/v1/audit-logs/{id}/` | Bearer access token |
| organization | GET | `/api/v1/branches/` | Bearer access token |
| organization | POST | `/api/v1/branches/` | Bearer access token |
| organization | GET | `/api/v1/branches/{id}/` | Bearer access token |
| organization | PATCH | `/api/v1/branches/{id}/` | Bearer access token |
| organization | POST | `/api/v1/branches/{id}/lifecycle/` | Bearer access token |
| organization | GET | `/api/v1/branches/{id}/members/` | Bearer access token |
| organization | POST | `/api/v1/branches/{id}/members/` | Bearer access token |
| organization | POST | `/api/v1/branches/{id}/members/{membership_id}/leave/` | Bearer access token |
| organization | POST | `/api/v1/branches/{id}/members/{membership_id}/primary/` | Bearer access token |
| organization | GET | `/api/v1/invitations/` | Bearer access token |
| organization | POST | `/api/v1/invitations/` | Bearer access token |
| organization | GET | `/api/v1/invitations/{id}/` | Bearer access token |
| organization | POST | `/api/v1/invitations/{id}/accept/` | Bearer access token |
| organization | POST | `/api/v1/invitations/{id}/resend/` | Bearer access token |
| organization | POST | `/api/v1/invitations/{id}/revoke/` | Bearer access token |
| organization | GET | `/api/v1/members/` | Bearer access token |
| organization | POST | `/api/v1/members/` | Bearer access token |
| organization | GET | `/api/v1/members/{id}/` | Bearer access token |
| organization | PATCH | `/api/v1/members/{id}/` | Bearer access token |
| organization | POST | `/api/v1/members/{id}/lifecycle/` | Bearer access token |
| organization | POST | `/api/v1/members/{id}/roles/` | Bearer access token |
| organization | GET | `/api/v1/organizations/current/` | Bearer access token |
| organization | PATCH | `/api/v1/organizations/current/` | Bearer access token |
| organization | POST | `/api/v1/organizations/current/lifecycle/` | Bearer access token |
| organization | GET | `/api/v1/organizations/current/settings/` | Bearer access token |
| organization | PATCH | `/api/v1/organizations/current/settings/` | Bearer access token |
| organization | GET | `/api/v1/permissions/` | Bearer access token |
| organization | GET | `/api/v1/role-assignments/` | Bearer access token |
| organization | GET | `/api/v1/roles/` | Bearer access token |
| organization | POST | `/api/v1/roles/` | Bearer access token |
| organization | GET | `/api/v1/roles/{id}/` | Bearer access token |
| organization | GET | `/api/v1/teams/` | Bearer access token |
| organization | POST | `/api/v1/teams/` | Bearer access token |
| organization | GET | `/api/v1/teams/{id}/` | Bearer access token |
| organization | PATCH | `/api/v1/teams/{id}/` | Bearer access token |
| organization | POST | `/api/v1/teams/{id}/lifecycle/` | Bearer access token |
| organization | GET | `/api/v1/teams/{id}/members/` | Bearer access token |
| organization | POST | `/api/v1/teams/{id}/members/` | Bearer access token |
| organization | POST | `/api/v1/teams/{id}/members/{membership_id}/leave/` | Bearer access token |
| organization | GET | `/health/live` | None at this layer |
| organization | GET | `/health/ready` | None at this layer |
| organization | POST | `/api/internal/v1/company-registration/` | Internal service token |
| organization | GET | `/api/internal/v1/identity-memberships/{identity_id}/` | Internal service token |
| organization | POST | `/api/internal/v1/invitations/validate/` | Internal service token |
| organization | POST | `/api/internal/v1/invitations/accept/` | Internal service token |
| organization | POST | `/api/internal/v1/invitations/accept-email/` | Internal service token |
| organization | POST | `/api/internal/v1/invitations/resume/` | Internal service token |
| identity | GET | `/health/live` | None at this layer |
| identity | GET | `/health/ready` | None at this layer |
| identity | POST | `/api/v1/auth/otp/request` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/otp/verify` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/refresh` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/logout` | Bearer access token |
| identity | POST | `/api/v1/auth/logout-all` | Bearer access token |
| identity | POST | `/api/v1/auth/context` | Bearer access token |
| identity | GET | `/api/v1/auth/me` | Bearer access token |
| identity | POST | `/api/v1/auth/qr/challenges` | No bearer; challenge/refresh proof where required |
| identity | GET | `/api/v1/auth/qr/challenges/{challenge_id}/status` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/qr/challenges/{challenge_id}/authorize` | Bearer access token |
| identity | POST | `/api/v1/auth/qr/challenges/{challenge_id}/consume` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/login` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/registration/company` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/invitations/password` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/registration/company/start` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/registration/company/resend` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/registration/company/verify` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/invitations/validate` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/invitations/resend` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/invitations/request` | No bearer; challenge/refresh proof where required |
| identity | POST | `/api/v1/auth/invitations/verify` | No bearer; challenge/refresh proof where required |
| identity | GET | `/api/v1/devices` | Bearer access token |
| identity | GET | `/api/v1/devices/{device_id}` | Bearer access token |
| identity | POST | `/api/v1/devices/{device_id}/revoke` | Bearer access token |
| identity | GET | `/api/v1/auth/sessions` | Bearer access token |
| identity | POST | `/api/v1/auth/sessions/{session_id}/revoke` | Bearer access token |
| user | GET | `/health/live` | None at this layer |
| user | GET | `/health/ready` | None at this layer |
| user | POST | `/internal/v1/users/block-check` | Internal service token |
| user | POST | `/internal/v1/users/projections` | Internal service token |
| user | GET | `/api/v1/users/me` | Bearer access token |
| user | PATCH | `/api/v1/users/me` | Bearer access token |
| user | GET | `/api/v1/users/me/preferences` | Bearer access token |
| user | PATCH | `/api/v1/users/me/preferences` | Bearer access token |
| user | POST | `/api/v1/users/{user_id}/block` | Bearer access token |
| user | DELETE | `/api/v1/users/{user_id}/block` | Bearer access token |
| user | GET | `/api/v1/users/me/privacy` | Bearer access token |
| user | PATCH | `/api/v1/users/me/privacy` | Bearer access token |
| user | GET | `/api/v1/users/me/blocked` | Bearer access token |
| user | GET | `/api/v1/users/search` | Bearer access token |
| user | GET | `/api/v1/users/{user_id}` | Bearer access token |
| user | POST | `/internal/v1/users/company-owner` | Internal service token |
| user | POST | `/internal/v1/users/provision` | Internal service token |
| conversation | GET | `/health/live` | None at this layer |
| conversation | GET | `/health/ready` | None at this layer |
| conversation | POST | `/api/v1/conversations/direct` | Bearer access token |
| conversation | POST | `/api/v1/conversations/groups` | Bearer access token |
| conversation | GET | `/api/v1/conversations` | Bearer access token |
| conversation | GET | `/api/v1/conversations/{cid}` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/members` | Bearer access token |
| conversation | DELETE | `/api/v1/conversations/{cid}/members/{mid}` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/leave` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/close` | Bearer access token |
| conversation | GET | `/api/v1/conversations/{cid}/members` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/members/{mid}/promote` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/members/{mid}/demote` | Bearer access token |
| conversation | POST | `/api/v1/conversations/{cid}/transfer-ownership` | Bearer access token |
| conversation | PATCH | `/api/v1/conversations/{cid}` | Bearer access token |
| conversation | PATCH | `/api/v1/conversations/{cid}/state` | Bearer access token |
| conversation | POST | `/internal/v1/conversations/{cid}/authorize` | Internal service token |
| messaging | GET | `/health/live` | None at this layer |
| messaging | GET | `/health/ready` | None at this layer |
| messaging | POST | `/api/v1/conversations/{conversation_id}/messages` | Bearer access token |
| messaging | GET | `/api/v1/conversations/{conversation_id}/messages` | Bearer access token |
| messaging | PATCH | `/api/v1/messages/{message_id}` | Bearer access token |
| messaging | DELETE | `/api/v1/messages/{message_id}` | Bearer access token |
| messaging | POST | `/api/v1/messages/{message_id}/reactions` | Bearer access token |
| messaging | DELETE | `/api/v1/messages/{message_id}/reactions/{reaction}` | Bearer access token |
| messaging | POST | `/api/v1/conversations/{conversation_id}/delivered` | Bearer access token |
| messaging | POST | `/api/v1/conversations/{conversation_id}/read` | Bearer access token |
| media | PUT | `/local-storage/{token}` | Signed capability in URL |
| media | GET | `/local-storage/{token}` | Signed capability in URL |
| media | GET | `/health/live` | None at this layer |
| media | GET | `/health/ready` | None at this layer |
| media | POST | `/api/v1/media/uploads` | Bearer access token |
| media | POST | `/api/v1/media/multipart` | Bearer access token |
| media | POST | `/api/v1/media/{media_id}/multipart/parts` | Bearer access token |
| media | GET | `/api/v1/media/{media_id}/multipart` | Bearer access token |
| media | POST | `/api/v1/media/{media_id}/multipart/complete` | Bearer access token |
| media | DELETE | `/api/v1/media/{media_id}/multipart` | Bearer access token |
| media | POST | `/api/v1/media/{media_id}/complete` | Bearer access token |
| media | GET | `/api/v1/media/{media_id}/download` | Bearer access token |
| media | DELETE | `/api/v1/media/{media_id}` | Bearer access token |
| notification | GET | `/health/live` | None at this layer |
| notification | GET | `/health/ready` | None at this layer |
| notification | PUT | `/api/v1/notifications/devices/current/token` | Bearer access token |
| notification | DELETE | `/api/v1/notifications/devices/current/token` | Bearer access token |
| notification | GET | `/api/v1/notifications/preferences` | Bearer access token |
| notification | PATCH | `/api/v1/notifications/preferences` | Bearer access token |
| notification | GET | `/api/v1/notifications` | Bearer access token |
| realtime | GET | `/health/live` | None at this layer |
| realtime | GET | `/health/ready` | None at this layer |
| realtime | WEBSOCKET | `/api/v1/realtime` | Access token in query; conversation authorization |
| gateway | GET | `/health/live` | None at this layer |
| gateway | GET | `/health/ready` | None at this layer |
| gateway | DELETE | `/{path:path}` | None at this layer |
| gateway | GET | `/{path:path}` | None at this layer |
| gateway | HEAD | `/{path:path}` | None at this layer |
| gateway | PATCH | `/{path:path}` | None at this layer |
| gateway | POST | `/{path:path}` | None at this layer |
| gateway | PUT | `/{path:path}` | None at this layer |
