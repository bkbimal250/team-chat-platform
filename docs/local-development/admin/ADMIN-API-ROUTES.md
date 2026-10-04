# Admin backend route reference

Source: current local OpenAPI and Organization permission/view implementations. All client calls reach Gateway through the same-origin admin bridge. No platform-wide access is inferred.

| Screen | Frontend route | Service | Method | API route | Auth / required permission | Status |
|---|---|---|---|---|---|---|
| Audit logs | `/audit-logs` | organization | GET | `/api/v1/audit-logs/` | audit.view | PASS |
| Audit logs | `/audit-logs` | organization | GET | `/api/v1/audit-logs/{id}/` | audit.view | PASS |
| Branches | `/branches` | organization | GET | `/api/v1/branches/` | branch.view | PASS |
| Branches | `/branches` | organization | POST | `/api/v1/branches/` | branch.create | PASS |
| Branches | `/branches` | organization | GET | `/api/v1/branches/{id}/` | branch.view | PASS |
| Branches | `/branches` | organization | PATCH | `/api/v1/branches/{id}/` | branch.update | PASS |
| Branches | `/branches` | organization | POST | `/api/v1/branches/{id}/lifecycle/` | branch.update | PASS |
| Branches | `/branches` | organization | GET | `/api/v1/branches/{id}/members/` | branch.view | PARTIAL |
| Branches | `/branches` | organization | POST | `/api/v1/branches/{id}/members/` | branch.create | PARTIAL |
| Branches | `/branches` | organization | POST | `/api/v1/branches/{id}/members/{membership_id}/leave/` | branch.create | PARTIAL |
| Branches | `/branches` | organization | POST | `/api/v1/branches/{id}/members/{membership_id}/primary/` | branch.create | PARTIAL |
| Invitations | `/invitations` | organization | GET | `/api/v1/invitations/` | invitation.view | PASS |
| Invitations | `/invitations` | organization | POST | `/api/v1/invitations/` | invitation.create | PASS |
| Invitations | `/invitations` | organization | GET | `/api/v1/invitations/{id}/` | invitation.view | PASS |
| Invitations | `/invitations` | organization | POST | `/api/v1/invitations/{id}/accept/` | invitation.accept | PARTIAL |
| Invitations | `/invitations` | organization | POST | `/api/v1/invitations/{id}/revoke/` | invitation.revoke | PASS |
| Members | `/members` | organization | GET | `/api/v1/members/` | member.view | PASS |
| Members | `/members` | organization | POST | `/api/v1/members/` | member.create | PASS |
| Members | `/members` | organization | GET | `/api/v1/members/{id}/` | member.view | PASS |
| Members | `/members` | organization | PATCH | `/api/v1/members/{id}/` | member.update | PASS |
| Members | `/members` | organization | POST | `/api/v1/members/{id}/lifecycle/` | member.update | PASS |
| Members | `/members` | organization | POST | `/api/v1/members/{id}/roles/` | role.manage | PASS |
| Organizations | `/organizations` | organization | GET | `/api/v1/organizations/current/` | organization.view | PASS |
| Organizations | `/organizations` | organization | PATCH | `/api/v1/organizations/current/` | organization.update | PASS |
| Organizations | `/organizations` | organization | POST | `/api/v1/organizations/current/lifecycle/` | organization.update | PASS |
| Organizations | `/settings` | organization | GET | `/api/v1/organizations/current/settings/` | organization.view | PASS |
| Organizations | `/settings` | organization | PATCH | `/api/v1/organizations/current/settings/` | organization.update | PASS |
| Roles | `/permissions` | organization | GET | `/api/v1/permissions/` | role.view | PARTIAL |
| Roles/session guard | `/role-assignments` | organization | GET | `/api/v1/role-assignments/` | role.view | PASS |
| Roles | `/roles` | organization | GET | `/api/v1/roles/` | role.view | PASS |
| Roles | `/roles` | organization | POST | `/api/v1/roles/` | role.manage | PARTIAL |
| Roles | `/roles` | organization | GET | `/api/v1/roles/{id}/` | role.view | PASS |
| Teams | `/teams` | organization | GET | `/api/v1/teams/` | team.view | PASS |
| Teams | `/teams` | organization | POST | `/api/v1/teams/` | team.create | PASS |
| Teams | `/teams` | organization | GET | `/api/v1/teams/{id}/` | team.view | PASS |
| Teams | `/teams` | organization | PATCH | `/api/v1/teams/{id}/` | team.update | PASS |
| Teams | `/teams` | organization | POST | `/api/v1/teams/{id}/lifecycle/` | team.update | PASS |
| Teams | `/teams` | organization | GET | `/api/v1/teams/{id}/members/` | team.view | PARTIAL |
| Teams | `/teams` | organization | POST | `/api/v1/teams/{id}/members/` | team.create | PARTIAL |
| Teams | `/teams` | organization | POST | `/api/v1/teams/{id}/members/{membership_id}/leave/` | team.create | PARTIAL |
| Login/session | `/login` | identity | POST | `/api/v1/auth/otp/request` | Public LOGIN challenge | PASS |
| Login/session | `/login` | identity | POST | `/api/v1/auth/otp/verify` | Public LOGIN challenge | PASS |
| Login/session | `session guard` | identity | POST | `/api/v1/auth/refresh` | Public LOGIN challenge | PASS |
| Login/session | `session guard` | identity | POST | `/api/v1/auth/logout` | Authenticated own account | PASS |
| Login/session | `session guard` | identity | GET | `/api/v1/auth/me` | Authenticated own account | PASS |
| Your devices/sessions | `/devices` | identity | GET | `/api/v1/devices` | Authenticated own account | PASS |
| Your devices/sessions | `/devices` | identity | GET | `/api/v1/devices/{device_id}` | Authenticated own account | PASS |
| Your devices/sessions | `/devices` | identity | POST | `/api/v1/devices/{device_id}/revoke` | Authenticated own account | PASS |
| Your devices/sessions | `/devices` | identity | GET | `/api/v1/auth/sessions` | Authenticated own account | PASS |
| Your devices/sessions | `/devices` | identity | POST | `/api/v1/auth/sessions/{session_id}/revoke` | Authenticated own account | PASS |
| Push registration | `/notifications` | notification | PUT | `/api/v1/notifications/devices/current/token` | Authenticated current member / own device | PARTIAL |
| Push registration | `/notifications` | notification | DELETE | `/api/v1/notifications/devices/current/token` | Authenticated current member / own device | PARTIAL |
| Notification preferences | `/settings` | notification | GET | `/api/v1/notifications/preferences` | Authenticated current member / own device | PASS |
| Notification preferences | `/settings` | notification | PATCH | `/api/v1/notifications/preferences` | Authenticated current member / own device | PASS |
| Own notifications | `/notifications` | notification | GET | `/api/v1/notifications` | Authenticated current member / own device | PASS |

Unavailable: platform organization list/create, billing plans, arbitrary tenant picker, organization-wide private conversations, cross-user devices/sessions, global analytics, notification read-state/browser push.

Newest-first cursor ordering is fixed; backend does not enable OrderingFilter. Resource status values are taken from schemas; lifecycle transitions are backend-authoritative. Organization invitations contain intended_role_id/expires_at and optional team_id/branch_id, not phone/email registration.

## GET /api/v1/audit-logs/
- AUTH/ROLE: audit.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Audit logs. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedAuditList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/audit-logs/{id}/
- AUTH/ROLE: audit.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Audit logs. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Audit"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/branches/
- AUTH/ROLE: branch.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedBranchList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/branches/
- AUTH/ROLE: branch.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/BranchRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "201": {
    "$ref": "#/components/schemas/Branch"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/branches/{id}/
- AUTH/ROLE: branch.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Branch"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/branches/{id}/
- AUTH/ROLE: branch.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PatchedBranchRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Branch"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/branches/{id}/lifecycle/
- AUTH/ROLE: branch.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Branch"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/branches/{id}/members/
- AUTH/ROLE: branch.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/BranchMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/branches/{id}/members/
- AUTH/ROLE: branch.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/BranchMembershipInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/BranchMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/branches/{id}/members/{membership_id}/leave/
- AUTH/ROLE: branch.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/BranchMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/branches/{id}/members/{membership_id}/primary/
- AUTH/ROLE: branch.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Branches. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/BranchMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/invitations/
- AUTH/ROLE: invitation.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Invitations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedInvitationList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/invitations/
- AUTH/ROLE: invitation.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Invitations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/InvitationRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "201": {
    "$ref": "#/components/schemas/Invitation"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/invitations/{id}/
- AUTH/ROLE: invitation.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Invitations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Invitation"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/invitations/{id}/accept/
- AUTH/ROLE: invitation.accept. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Invitations. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/AcceptInvitationInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Invitation"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/invitations/{id}/revoke/
- AUTH/ROLE: invitation.revoke. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Invitations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Invitation"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/members/
- AUTH/ROLE: member.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedMemberList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/members/
- AUTH/ROLE: member.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/MemberRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "201": {
    "$ref": "#/components/schemas/Member"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/members/{id}/
- AUTH/ROLE: member.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Member"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/members/{id}/
- AUTH/ROLE: member.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PatchedMemberRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Member"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/members/{id}/lifecycle/
- AUTH/ROLE: member.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Member"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/members/{id}/roles/
- AUTH/ROLE: role.manage. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Members. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/RoleAssignmentInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Member"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/organizations/current/
- AUTH/ROLE: organization.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Organizations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Organization"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/organizations/current/
- AUTH/ROLE: organization.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Organizations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PatchedOrganizationRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Organization"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/organizations/current/lifecycle/
- AUTH/ROLE: organization.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Organizations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Organization"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/organizations/current/settings/
- AUTH/ROLE: organization.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Organizations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Settings"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/organizations/current/settings/
- AUTH/ROLE: organization.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Organizations. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PatchedSettingsRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Settings"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/permissions/
- AUTH/ROLE: role.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Roles. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedPermissionList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/role-assignments/
- AUTH/ROLE: role.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Roles/session guard. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedRoleAssignmentList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/roles/
- AUTH/ROLE: role.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Roles. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedRoleList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/roles/
- AUTH/ROLE: role.manage. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Roles. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/CustomRoleInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "201": {
    "$ref": "#/components/schemas/Role"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/roles/{id}/
- AUTH/ROLE: role.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Roles. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Role"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/teams/
- AUTH/ROLE: team.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/PaginatedTeamList"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/teams/
- AUTH/ROLE: team.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/TeamRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "201": {
    "$ref": "#/components/schemas/Team"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/teams/{id}/
- AUTH/ROLE: team.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Team"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/teams/{id}/
- AUTH/ROLE: team.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PatchedTeamRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Team"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/teams/{id}/lifecycle/
- AUTH/ROLE: team.update. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/Team"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/teams/{id}/members/
- AUTH/ROLE: team.view. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/TeamMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/teams/{id}/members/
- AUTH/ROLE: team.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/TeamMembershipInputRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/TeamMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/teams/{id}/members/{membership_id}/leave/
- AUTH/ROLE: team.create. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Teams. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/TeamMembership"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/auth/otp/request
- AUTH/ROLE: Public LOGIN challenge. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Login/session. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/OTPRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "202": {
    "$ref": "#/components/schemas/OTPRequestResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/auth/otp/verify
- AUTH/ROLE: Public LOGIN challenge. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Login/session. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/OTPVerifyRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/TokenResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/auth/refresh
- AUTH/ROLE: Public LOGIN challenge. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Login/session. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/RefreshRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/TokenResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/auth/logout
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Login/session. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/RevokeResponse"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/auth/me
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Login/session. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/MeResponse"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/devices
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Your devices/sessions. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "items": {
      "$ref": "#/components/schemas/DeviceResponse"
    },
    "type": "array",
    "title": "Response Devices Api V1 Devices Get"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/devices/{device_id}
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Your devices/sessions. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/DeviceResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/devices/{device_id}/revoke
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Your devices/sessions. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/RevokeResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/auth/sessions
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Your devices/sessions. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "items": {
      "$ref": "#/components/schemas/SessionResponse"
    },
    "type": "array",
    "title": "Response Sessions Api V1 Auth Sessions Get"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## POST /api/v1/auth/sessions/{session_id}/revoke
- AUTH/ROLE: Authenticated own account. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Your devices/sessions. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {
    "$ref": "#/components/schemas/RevokeResponse"
  },
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PUT /api/v1/notifications/devices/current/token
- AUTH/ROLE: Authenticated current member / own device. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Push registration. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/TokenRequest"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {},
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## DELETE /api/v1/notifications/devices/current/token
- AUTH/ROLE: Authenticated current member / own device. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Push registration. UI coverage: PARTIAL; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {},
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/notifications/preferences
- AUTH/ROLE: Authenticated current member / own device. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Notification preferences. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {},
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## PATCH /api/v1/notifications/preferences
- AUTH/ROLE: Authenticated current member / own device. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Notification preferences. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{
  "$ref": "#/components/schemas/PreferencePatch"
}
```
- RESPONSE (actual schema references):
```json
{
  "200": {},
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.

## GET /api/v1/notifications
- AUTH/ROLE: Authenticated current member / own device. Backend membership and tenant validation remain mandatory.
- ADMIN SCREEN: Own notifications. UI coverage: PASS; PARTIAL means some actions remain Postman-only or user-owned.
- REQUEST (actual schema reference):
```json
{}
```
- RESPONSE (actual schema references):
```json
{
  "200": {},
  "422": {
    "$ref": "#/components/schemas/HTTPValidationError"
  }
}
```
- ERRORS: 401 token/session, 403 permission, 404 resource/cross-tenant, 400/422 validation; lifecycle/delegation protections may reject valid JSON.
- POSTMAN STEPS: Select Gateway base URL; set private Bearer token from real OTP verification; replace UUID placeholders with IDs from the same tenant; provide only writable schema fields; inspect returned status. See adjacent service OpenAPI component definitions for referenced schemas.


## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
