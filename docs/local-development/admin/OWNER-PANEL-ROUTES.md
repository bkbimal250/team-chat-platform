# Owner Panel routes

All HTTP calls below use `/api/gateway` in the browser. Protected pages render only after Identity session and Organization permissions resolve.

| Screen | Frontend route | API | Realtime | Status |
|---|---|---|---|---|
| Login | `/login` | POST `/api/v1/auth/login`, me/roles/assignments/profile | Not applicable | Real |
| Registration | `/register` | POST `/api/v1/auth/registration/company` | Not applicable | Real |
| Dashboard | `/dashboard` | current organization, members, branches, teams, invitations, audit | API refresh fallback | Real bounded counts |
| Company | `/organizations` | GET/PATCH `/api/v1/organizations/current/` | API refresh fallback | Current company only |
| Company detail | `/organizations/{current_id}` | current organization and scoped resources/settings | API refresh fallback | Unknown IDs rejected |
| Branches | `/branches` | branches list/create/detail/edit/lifecycle | API refresh fallback | Real |
| Teams | `/teams` | teams list/create/detail/edit/lifecycle | API refresh fallback | Real |
| Members/detail | `/members` | members, roles, branches/teams membership actions | API refresh fallback | Real; detail dialog |
| Invitations | `/invitations` | list/create/resend/revoke | API refresh fallback | Real; delivery unavailable |
| Devices | `/devices` | `/api/v1/devices`, `/api/v1/auth/sessions`, revoke | API refresh fallback | Own account only |
| Notifications | `/notifications` | `/api/v1/notifications` | API refresh fallback | List only; read-state unavailable |
| Profile | `/profile` | GET/PATCH `/api/v1/users/me` | Not applicable | Real supported fields |
| Settings | `/settings` | organization settings, users/me preferences/privacy, notification preferences | API refresh fallback for organization/notifications | Real supported settings |
| Roles/Audit | `/roles`, `/audit-logs` | authorized Organization contracts | API refresh fallback for audit | Real |

Unsupported conversation moderation, platform infrastructure and cross-user security administration are not represented as working tools.

## Verified limitation

The current Organization resend endpoint requires a recipient phone. Email-only invitations can be created and revoked, but link regeneration is unavailable and is explicitly marked in the UI. No backend workaround or identity change was made.
