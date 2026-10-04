# Postman testing guide

Last verified: 2026-10-04. Source: running local OpenAPI schemas.

Import the collection/environment under `../postman/`. Examples are schema-derived templates, not working credentials. Replace placeholders and check required fields in the request schema. PARTIAL means schema/import verified, not that every mutation was executed.

**YOU DO THIS MANUALLY:** request a development OTP for an explicitly seeded phone, copy `development_code` privately into verify request, then use the returned access token. Do not share the environment after tokens are captured.

| Service | Method | Route | Auth | Purpose | Call through | Status |

|---|---|---|---|---|---|---|

| organization | GET | `/api/schema/` | access token | schema_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/audit-logs/` | access token | v1_audit_logs_list | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/audit-logs/{id}/` | access token | v1_audit_logs_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/branches/` | access token | v1_branches_list | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/branches/` | access token | v1_branches_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/branches/{id}/` | access token | v1_branches_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | PATCH | `/api/v1/branches/{id}/` | access token | v1_branches_partial_update | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/branches/{id}/lifecycle/` | access token | v1_branches_lifecycle_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/branches/{id}/members/` | access token | v1_branches_members_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/branches/{id}/members/` | access token | v1_branches_members_create | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/branches/{id}/members/{membership_id}/leave/` | access token | v1_branches_members_leave_create | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/branches/{id}/members/{membership_id}/primary/` | access token | v1_branches_members_primary_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/invitations/` | access token | v1_invitations_list | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/invitations/` | access token | v1_invitations_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/invitations/{id}/` | access token | v1_invitations_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/invitations/{id}/accept/` | access token | v1_invitations_accept_create | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/invitations/{id}/revoke/` | access token | v1_invitations_revoke_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/members/` | access token | v1_members_list | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/members/` | access token | v1_members_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/members/{id}/` | access token | v1_members_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | PATCH | `/api/v1/members/{id}/` | access token | v1_members_partial_update | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/members/{id}/lifecycle/` | access token | v1_members_lifecycle_create | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/members/{id}/roles/` | access token | v1_members_roles_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/organizations/current/` | access token | v1_organizations_current_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | PATCH | `/api/v1/organizations/current/` | access token | v1_organizations_current_partial_update | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/organizations/current/lifecycle/` | access token | v1_organizations_current_lifecycle_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/organizations/current/settings/` | access token | v1_organizations_current_settings_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | PATCH | `/api/v1/organizations/current/settings/` | access token | v1_organizations_current_settings_partial_update | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/permissions/` | access token | v1_permissions_list | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/role-assignments/` | access token | v1_role_assignments_list | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/roles/` | access token | v1_roles_list | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/roles/` | access token | v1_roles_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/roles/{id}/` | access token | v1_roles_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/teams/` | access token | v1_teams_list | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/teams/` | access token | v1_teams_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/teams/{id}/` | access token | v1_teams_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | PATCH | `/api/v1/teams/{id}/` | access token | v1_teams_partial_update | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/teams/{id}/lifecycle/` | access token | v1_teams_lifecycle_create | THROUGH GATEWAY | PARTIAL |

| organization | GET | `/api/v1/teams/{id}/members/` | access token | v1_teams_members_retrieve | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/teams/{id}/members/` | access token | v1_teams_members_create | THROUGH GATEWAY | PARTIAL |

| organization | POST | `/api/v1/teams/{id}/members/{membership_id}/leave/` | access token | v1_teams_members_leave_create | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| identity | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| identity | POST | `/api/v1/auth/otp/request` | none | Otp Request | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/otp/verify` | none | Otp Verify | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/refresh` | none | Refresh | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/logout` | access token | Logout | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/logout-all` | access token | Logout All | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/context` | access token | Switch Context | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/api/v1/auth/me` | access token | Me | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/qr/challenges` | none | Qr Create | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/api/v1/auth/qr/challenges/{challenge_id}/status` | none | Qr Status | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/qr/challenges/{challenge_id}/authorize` | access token | Qr Authorize | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/qr/challenges/{challenge_id}/consume` | none | Qr Consume | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/api/v1/devices` | access token | Devices | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/api/v1/devices/{device_id}` | access token | Device | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/devices/{device_id}/revoke` | access token | Revoke Device | THROUGH GATEWAY | PARTIAL |

| identity | GET | `/api/v1/auth/sessions` | access token | Sessions | THROUGH GATEWAY | PARTIAL |

| identity | POST | `/api/v1/auth/sessions/{session_id}/revoke` | access token | Revoke | THROUGH GATEWAY | PARTIAL |

| user | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| user | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| user | POST | `/internal/v1/users/block-check` | service token | Block Check | DIRECT SERVICE | PARTIAL |

| user | POST | `/internal/v1/users/projections` | service token | Projections | DIRECT SERVICE | PARTIAL |

| user | GET | `/api/v1/users/me` | access token | Me | THROUGH GATEWAY | PARTIAL |

| user | PATCH | `/api/v1/users/me` | access token | Update Me | THROUGH GATEWAY | PARTIAL |

| user | GET | `/api/v1/users/me/preferences` | access token | Preferences | THROUGH GATEWAY | PARTIAL |

| user | PATCH | `/api/v1/users/me/preferences` | access token | Update Preferences | THROUGH GATEWAY | PARTIAL |

| user | POST | `/api/v1/users/{user_id}/block` | access token | Block | THROUGH GATEWAY | PARTIAL |

| user | DELETE | `/api/v1/users/{user_id}/block` | access token | Unblock | THROUGH GATEWAY | PARTIAL |

| user | GET | `/api/v1/users/me/privacy` | access token | Privacy | THROUGH GATEWAY | PARTIAL |

| user | PATCH | `/api/v1/users/me/privacy` | access token | Update Privacy | THROUGH GATEWAY | PARTIAL |

| user | GET | `/api/v1/users/me/blocked` | access token | Blocked Users | THROUGH GATEWAY | PARTIAL |

| user | GET | `/api/v1/users/search` | access token | Search Users | THROUGH GATEWAY | PARTIAL |

| user | GET | `/api/v1/users/{user_id}` | access token | Get Profile | THROUGH GATEWAY | PARTIAL |

| conversation | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| conversation | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| conversation | POST | `/api/v1/conversations/direct` | access token | Direct | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/groups` | access token | Group | THROUGH GATEWAY | PARTIAL |

| conversation | GET | `/api/v1/conversations` | access token | List Conversations | THROUGH GATEWAY | PARTIAL |

| conversation | GET | `/api/v1/conversations/{cid}` | access token | Get | THROUGH GATEWAY | PARTIAL |

| conversation | PATCH | `/api/v1/conversations/{cid}` | access token | Update | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/members` | access token | Add | THROUGH GATEWAY | PARTIAL |

| conversation | GET | `/api/v1/conversations/{cid}/members` | access token | Members | THROUGH GATEWAY | PARTIAL |

| conversation | DELETE | `/api/v1/conversations/{cid}/members/{mid}` | access token | Remove | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/leave` | access token | Leave | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/close` | access token | Close | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/members/{mid}/promote` | access token | Promote | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/members/{mid}/demote` | access token | Demote | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/api/v1/conversations/{cid}/transfer-ownership` | access token | Transfer | THROUGH GATEWAY | PARTIAL |

| conversation | PATCH | `/api/v1/conversations/{cid}/state` | access token | State | THROUGH GATEWAY | PARTIAL |

| conversation | POST | `/internal/v1/conversations/{cid}/authorize` | service token | Authorize Send | DIRECT SERVICE | PARTIAL |

| messaging | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| messaging | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| messaging | POST | `/api/v1/conversations/{conversation_id}/messages` | access token | Create | THROUGH GATEWAY | PARTIAL |

| messaging | GET | `/api/v1/conversations/{conversation_id}/messages` | access token | History | THROUGH GATEWAY | PARTIAL |

| messaging | PATCH | `/api/v1/messages/{message_id}` | access token | Edit | THROUGH GATEWAY | PARTIAL |

| messaging | DELETE | `/api/v1/messages/{message_id}` | access token | Delete | THROUGH GATEWAY | PARTIAL |

| messaging | POST | `/api/v1/messages/{message_id}/reactions` | access token | Add Reaction | THROUGH GATEWAY | PARTIAL |

| messaging | DELETE | `/api/v1/messages/{message_id}/reactions/{reaction}` | access token | Remove Reaction | THROUGH GATEWAY | PARTIAL |

| messaging | POST | `/api/v1/conversations/{conversation_id}/delivered` | access token | Delivered | THROUGH GATEWAY | PARTIAL |

| messaging | POST | `/api/v1/conversations/{conversation_id}/read` | access token | Read | THROUGH GATEWAY | PARTIAL |

| media | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| media | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| media | POST | `/api/v1/media/uploads` | access token | Initiate Upload | THROUGH GATEWAY | PARTIAL |

| media | POST | `/api/v1/media/multipart` | access token | Initiate Multipart | THROUGH GATEWAY | PARTIAL |

| media | POST | `/api/v1/media/{media_id}/multipart/parts` | access token | Multipart Parts | THROUGH GATEWAY | PARTIAL |

| media | GET | `/api/v1/media/{media_id}/multipart` | access token | Multipart Resume | THROUGH GATEWAY | PARTIAL |

| media | DELETE | `/api/v1/media/{media_id}/multipart` | access token | Abort Multipart | THROUGH GATEWAY | PARTIAL |

| media | POST | `/api/v1/media/{media_id}/multipart/complete` | access token | Complete Multipart | THROUGH GATEWAY | PARTIAL |

| media | POST | `/api/v1/media/{media_id}/complete` | access token | Complete Upload | THROUGH GATEWAY | PARTIAL |

| media | GET | `/api/v1/media/{media_id}/download` | access token | Download | THROUGH GATEWAY | PARTIAL |

| media | DELETE | `/api/v1/media/{media_id}` | access token | Delete | THROUGH GATEWAY | PARTIAL |

| notification | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| notification | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |

| notification | PUT | `/api/v1/notifications/devices/current/token` | access token | Put Token | THROUGH GATEWAY | PARTIAL |

| notification | DELETE | `/api/v1/notifications/devices/current/token` | access token | Delete Token | THROUGH GATEWAY | PARTIAL |

| notification | GET | `/api/v1/notifications/preferences` | access token | Get Preferences | THROUGH GATEWAY | PARTIAL |

| notification | PATCH | `/api/v1/notifications/preferences` | access token | Patch Preferences | THROUGH GATEWAY | PARTIAL |

| notification | GET | `/api/v1/notifications` | access token | List Notifications | THROUGH GATEWAY | PARTIAL |

| realtime | GET | `/health/live` | none | Live | DIRECT SERVICE | PARTIAL |

| realtime | GET | `/health/ready` | none | Ready | DIRECT SERVICE | PARTIAL |
## Organization administration

See [admin route/permission matrix](../admin/ADMIN-API-ROUTES.md) and [admin manual checks](../admin/ADMIN-MANUAL-TESTING.md). Use current tenant/member role assignments, not fabricated platform-admin capabilities. Own devices/notifications are not cross-user admin APIs.


## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
