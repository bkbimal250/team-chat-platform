# GlobalChat public API ingress contract

The gateway preserves every existing public path and never exposes downstream health, docs,
admin, schema, or internal service endpoints. All owning services continue to authenticate and
authorize requests. Request and response models remain the downstream OpenAPI contracts.

| Owner | Public namespace | Operations and behavior |
|---|---|---|
| Identity | `/api/v1/auth/**`, `/api/v1/devices/**` | OTP request/verify, refresh, logout, context, current identity, QR challenge flow, session list/revoke and device list/detail/revoke. Public OTP endpoints are unauthenticated; token/session/device/context operations use their existing bearer requirements. JSON bodies and path IDs; no streams. |
| User | `/api/v1/users/**` | Current profile/preferences/privacy, block/unblock/list, search and profile lookup. Existing bearer authentication; search query parameters; JSON only. |
| Organization | `/api/v1/organizations/**`, `/branches/**`, `/teams/**`, `/members/**`, `/invitations/**`, `/roles/**`, `/permissions/**`, `/role-assignments/**`, `/audit-logs/**` | DRF list/detail/create/update/delete and declared lifecycle, membership, invitation and role actions. Existing bearer/tenant authorization, pagination/filter query parameters and JSON bodies. |
| Conversation | `/api/v1/conversations/**` except messaging subresources | Direct/group creation, list/detail/update/state, membership, role, ownership, leave and close operations. Existing bearer auth; list filters/pagination; JSON only. |
| Messaging | `/api/v1/messages/**`, `/api/v1/conversations/{id}/messages/**`, `/delivered`, `/read` | Send/list/edit/delete messages, reactions, delivery/read receipts. Existing bearer auth; message pagination query parameters; JSON only. |
| Media | `/api/v1/media/**` | Upload and multipart authorization/metadata, completion, status, download signing and delete. Existing bearer auth. Responses provide presigned S3 operations; large object bytes remain client-to-S3 and never transit the gateway. |
| Notification | `/api/v1/notifications/**` | Device token put/delete and preference get/patch. Existing bearer auth; JSON only. |

The intentional path overlap is `/api/v1/conversations/{id}/{messages,delivered,read}`. These
specific subresources are resolved to Messaging before the remaining Conversation namespace.
The routing table and tests make this precedence executable.

## Audited operations

- Identity: `POST auth/otp/request`, `POST auth/otp/verify`, `POST auth/refresh`, `POST
  auth/logout`, `POST auth/logout-all`, `POST auth/context`, `GET auth/me`, and the QR challenge
  create/status/authorize/consume operations; `GET devices`, `GET devices/{id}`, `POST
  devices/{id}/revoke`; `GET auth/sessions`, `POST auth/sessions/{id}/revoke`.
- User: `GET/PATCH users/me`, `GET/PATCH users/me/preferences`, `GET/PATCH users/me/privacy`,
  `GET users/me/blocked`, `GET users/search`, `GET users/{id}`, and `POST/DELETE
  users/{id}/block`.
- Organization: `GET/PATCH organizations/current`, `GET/PATCH organizations/current/settings`,
  `POST organizations/current/lifecycle`; list/create/detail/patch/lifecycle for branches, teams,
  and members where implemented; branch/team member list/add/leave plus branch primary; member role
  assignment; invitation list/create/detail/accept/revoke; role list/create/detail; permission and
  role-assignment lists; audit-log list/detail. Standard list endpoints accept their declared DRF
  pagination, search, ordering, and filter query parameters.
- Conversation: `POST conversations/direct`, `POST conversations/groups`, `GET conversations`,
  `GET/PATCH conversations/{id}`, member add/remove/list/promote/demote, leave, close, ownership
  transfer, and state update.
- Messaging: `POST/GET conversations/{id}/messages`, `PATCH/DELETE messages/{id}`, `POST/DELETE
  messages/{id}/reactions[/{reaction}]`, `POST conversations/{id}/delivered`, and `POST
  conversations/{id}/read`.
- Media: upload initialization, multipart initialization/part signing/status/complete/abort,
  single-upload completion, download signing, and delete under `media`. These are metadata JSON
  operations; presigned object transfer URLs are returned to the client.
- Notification: `PUT/DELETE notifications/devices/current/token` and `GET/PATCH
  notifications/preferences`.

All listed operations return the owning service's existing JSON/status contract. There are no
public byte-streaming or multipart-file-body endpoints in these seven service APIs. Organization
DRF endpoints and every non-OTP identity endpoint apply their existing action-specific bearer and
tenant permissions; the remaining services derive identity and organization context from the
forwarded bearer JWT. Only Identity OTP request/verification and QR status/consume retain their
current public authentication behavior.

Browser clients use `https://api.michat.in`; realtime remains `wss://ws.michat.in`.
