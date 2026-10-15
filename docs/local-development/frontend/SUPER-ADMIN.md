# SUPER ADMIN

Platform authority is persistent in Identity's `platform_grants` table and is separate from company membership roles. A company OWNER, ADMIN, or MEMBER receives no platform permission without an explicit active grant.

The initial local Super Admin is created by a trusted local operator only. First create and sign in to an active account through the ordinary company flow, then run from `services/identity-service`:

```powershell
.venv\Scripts\python.exe -m app.platform_operator <identity-uuid> SUPER_ADMIN
```

The command does not create accounts, accept emails, print credentials, or expose an HTTP self-grant path. It records an operator audit row and prevents removing the final active Super Admin. Use `ADMIN` for the lower read-only platform role, or `revoke` to deactivate an existing grant.

The C1 APIs are metadata-only: `/api/v1/platform/me`, identities, sessions, audit and the authorized organization structure endpoints. They never return passwords, hashes, refresh tokens, OTPs, provider credentials, private messages, or private media. Full platform screens remain C2 work.
