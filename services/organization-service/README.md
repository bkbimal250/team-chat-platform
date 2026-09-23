# Organization Service

Django 5.2 LTS / DRF on Python 3.12, PostgreSQL 17 and RabbitMQ 4. This service exclusively owns `organization_db`. No other service may query its tables. Dependencies are pinned in `uv.lock`.

## Run with Docker

From the repository root:

```powershell
Copy-Item .env.example .env # only when .env does not already exist
# Replace SECRET_KEY, DB_PASSWORD and RABBITMQ_PASSWORD placeholders.
docker compose up -d --build
docker compose ps
docker compose logs --tail 100 organization-service outbox-worker
docker compose exec organization-service python manage.py createsuperuser
docker compose exec organization-service python manage.py provision_organization --name "Example" --slug example --owner-name "Owner" --owner-user-id "11111111-1111-4111-8111-111111111111"
```

Provisioning prints `organization_id` and `owner_member_id`. Use the latter as `X-Dev-Member-ID` in Swagger's Authorize dialog. The UUID given as `owner-user-id` is only an external identity reference; this command creates no product credentials and does not verify identity. Organizations are provisioned through operator commands, not a public unauthenticated endpoint.

```powershell
$memberId = 'replace-with-owner-member-id'
Invoke-RestMethod http://localhost:8000/api/v1/organizations/current/ -Headers @{'X-Dev-Member-ID'=$memberId}
Invoke-RestMethod http://localhost:8000/api/v1/branches/ -Method Post -ContentType application/json -Headers @{'X-Dev-Member-ID'=$memberId} -Body '{"name":"Mumbai","code":"MUM-01","country":"IN"}'
```

Endpoints:

| URL | Purpose |
|---|---|
| http://localhost:8000/health/live | Process liveness |
| http://localhost:8000/health/ready | PostgreSQL readiness |
| http://localhost:8000/api/docs/ | Development Swagger |
| http://localhost:8000/api/redoc/ | Development Redoc |
| http://localhost:8000/api/schema/ | OpenAPI schema |
| http://localhost:8000/admin/ | Operator administration |
| http://localhost:15672 | Local RabbitMQ management; user `organization_service`, password from `.env` |

Readiness deliberately does not depend on RabbitMQ: the API can commit changes to its durable outbox during a broker outage. Monitor pending-event age, failed count, and worker/broker availability separately. The worker reconnects after outages. The archive queue retains events until an operator or a future consumer consumes them; plan capacity and retention before production.

## Local Python development and validation

Install Python and `uv`, then run from `services/organization-service`. The PowerShell helper reads the root `.env`, sets local dependency addresses and uses the migrator account for development/tests only.

```powershell
python -m pip install uv
python -m uv sync --python 3.12 --frozen
./dev.ps1 python manage.py check
./dev.ps1 python manage.py migrate --noinput
./dev.ps1 python manage.py makemigrations --check --dry-run
./dev.ps1 python manage.py collectstatic --noinput
./dev.ps1 ruff format .
./dev.ps1 ruff check .
./dev.ps1 pytest -q
./dev.ps1 python manage.py spectacular --file openapi.yaml --validate --fail-on-warn
./dev.ps1 python manage.py runserver 127.0.0.1:8001
```

On Linux/macOS, export the service `.env.example` values with real secrets (PostgreSQL host `127.0.0.1`, port `55432`) and run equivalent `uv run ...` commands. Python 3.12 is downloaded by `uv` when needed. Tests always use PostgreSQL, create `test_organization_db`, and require a dedicated development/test database account with CREATEDB. The production runtime account must not have that permission. The full test suite requires RabbitMQ; `pytest -m 'not integration'` excludes the live broker test but still uses PostgreSQL.

## Operator commands

```powershell
docker compose run --rm migrate
docker compose exec organization-service python manage.py createsuperuser
docker compose exec organization-service python manage.py publish_outbox --once
docker compose exec organization-service python manage.py retry_outbox EVENT_UUID
docker compose exec organization-service python manage.py expire_invitations --limit 500
docker compose exec organization-service python manage.py organization_lifecycle ORGANIZATION_UUID SUSPENDED
docker compose exec organization-service python manage.py organization_lifecycle ORGANIZATION_UUID ACTIVE
docker compose exec organization-service python manage.py link_member ORGANIZATION_UUID MEMBER_UUID PLATFORM_USER_UUID
```

Use `link_member` only after an operator has established the external identity reference. Then POST `{"status":"ACTIVE"}` to the member lifecycle endpoint. Identity linking will become a verified service contract in Phase 2. Public member payloads cannot overwrite `user_id`.

Django Admin provides searchable, filtered, read-only domain inspection, plus normal operator-user management. Domain writes use application services/API/commands so audit/outbox behavior cannot be silently bypassed. There are no mass-delete domain actions. Audit UPDATE/DELETE is additionally blocked by a PostgreSQL trigger. Failed outbox requeue is an explicit command preserving the original event ID.

## API inventory

All resource identifiers below are UUIDs. Lists return `{next, previous, results}`; page size defaults to 50 and is capped at 100. Ordering is descending `created_at`, then `id`. DRF's position-plus-offset cursor handles equal timestamps; it is not a snapshot of concurrent writes. Tenant resources are fetched through the shared selector and return 404 outside the tenant.

| Path under `/api/v1/` | Methods | Permission |
|---|---|---|
| `organizations/current/` | GET, PATCH | organization.view / organization.update |
| `organizations/current/settings/` | GET, PATCH | organization.view / organization.update |
| `organizations/current/lifecycle/` | POST | organization.update |
| `branches/`, `teams/`, `members/` | GET, POST | resource.view / resource.create |
| `branches/{id}/`, `teams/{id}/`, `members/{id}/` | GET, PATCH | resource.view / resource.update |
| `branches/{id}/lifecycle/`, `teams/{id}/lifecycle/` | POST | resource.update; deletion additionally resource.delete |
| `members/{id}/lifecycle/` | POST | member.update; departure additionally member.remove |
| `teams/{id}/members/`, `branches/{id}/members/` | GET, POST | resource.view / resource.update |
| `teams/{id}/members/{membership_id}/leave/` | POST | team.update |
| `branches/{id}/members/{membership_id}/leave/` | POST | branch.update |
| `branches/{id}/members/{membership_id}/primary/` | POST | branch.update |
| `members/{id}/roles/` | POST | role.manage; `{role_id, remove?: false}` |
| `roles/`, `roles/{id}/` | GET | role.view |
| `roles/` | POST | role.manage; `{name, permission_codes}` creates CUSTOM role |
| `permissions/`, `role-assignments/` | GET | role.view |
| `invitations/`, `invitations/{id}/` | GET | invitation.view |
| `invitations/` | POST | invitation.create |
| `invitations/{id}/revoke/` | POST | invitation.revoke |
| `invitations/{id}/accept/` | POST | invitation.accept; trusted operator business operation `{member_id}` |
| `audit-logs/`, `audit-logs/{id}/` | GET | audit.view |

No hard-delete endpoints exist. Invitation acceptance is an operator/trusted business operation in Phase 1, not end-user onboarding. It requires an active linked member; references are checked within the tenant. Repeated acceptance for the same member is idempotent, and acceptance for a different member conflicts. Revocation is also idempotent. `expire_invitations` materializes expiration; acceptance rejects expired timestamps even before that command runs.

Filters: members `status`, `team`, `branch`, `role`, `search` (display name/employee code); teams `branch`, `status`, `search` (name); branches `status`, `city`, `search` (name/code); invitations `status`; role assignments `member`, `role`; audits `action`, `resource_type`. Arbitrary field filtering is not enabled.

Errors use stable codes:

```json
{"error":{"code":"TEAM_MEMBERSHIP_EXISTS","message":"The operation conflicts with an existing resource or relationship.","details":{"detail":"..."},"correlation_id":"request-123"}}
```

Other codes include `NOT_FOUND`, `PERMISSION_DENIED`, `NOT_AUTHENTICATED`, `VALIDATION_ERROR`, `MEMBER_ALREADY_EXISTS`, `BRANCH_CODE_EXISTS`, `BRANCH_MEMBERSHIP_EXISTS`, `PRIMARY_BRANCH_EXISTS`, `CONSTRAINT_CONFLICT`, `INVALID_TRANSITION`, `LAST_OWNER`, `ROLE_ESCALATION_DENIED`, `TENANT_LIMIT_REACHED`, and `INVITATION_UNAVAILABLE`. Client code must use codes/status, not parse English text.

## Authorization and tenant boundaries

`TenantContext` separates organization, member and platform-user UUIDs, permissions, and correlation ID. The local-only adapter resolves an ACTIVE member in an ACTIVE organization from `X-Dev-Member-ID`, then calculates permissions from database assignments. It ignores arbitrary tenant/permission headers. Production settings reject this adapter and fail closed until a verified Phase 2 adapter is installed. A future adapter must verify issuer, signature, audience, expiry, revocation/membership and tenant binding before constructing this context; never accept raw gateway headers from an untrusted network.

Permission evaluation is centralized. Commands recheck active membership and current permissions under a tenant row lock. Roles are per tenant, permissions are a global stable registry. OWNER has all permissions. ADMIN excludes billing.manage, role.manage and invitation.accept. MANAGER has basic reads, team creation/update and invitation creation; MEMBER has basic reads. Roles cannot delegate permissions the actor lacks. Only an owner can delegate OWNER, and the last active owner cannot be removed, suspended or lose ownership. Custom roles can be created and assigned; editing seeded role permission sets is intentionally unavailable.

`Member` is the organization membership, with its own UUID. Non-null `user_id` is unique within an organization but may occur in other organizations. Employee codes are also unique per tenant when supplied. Branch codes are case-sensitive unique per organization. Team names are case-sensitive unique per organization, including disabled/deleted rows; this reserves names and preserves historical references.

Shared tenant selectors scope API reads; service validation checks indirect references; PostgreSQL composite `(organization_id, reference_id)` foreign keys reject cross-tenant relationships even through bulk writes/raw SQL. Tenant ownership is immutable. Scoped ORM methods are explicit; unscoped ORM access is reserved for operators and internal cross-tenant jobs, not endpoints. PostgreSQL RLS is not used in this phase.

Tenant row locks serialize mutations within one organization, while different tenants proceed independently. This simplifies capacity, owner, role and lifecycle race safety; measure throughput before relaxing this conservative lock. Partial unique indexes enforce active team/branch memberships and one active primary branch. Invitation row locks and outbox row locks protect concurrent transitions/publishing.

## Configuration and production deployment

| Variable | Purpose |
|---|---|
| SECRET_KEY | Django operator sessions/security; required secret |
| DATABASE_URL | PostgreSQL URL; required; SQLite rejected |
| RABBITMQ_URL | Service-specific AMQP URL/vhost; required |
| DB_PASSWORD, RABBITMQ_PASSWORD | Development Compose secrets |
| DJANGO_SETTINGS_MODULE | `config.settings.local` or `config.settings.production` |
| ENVIRONMENT | `local` for local docs; non-local required in production |
| DEBUG | Optional local debug; production forces false |
| DEV_CONTEXT_ENABLED | Explicit unsafe local identity adapter; rejected in production |
| ALLOWED_HOSTS | Comma-separated host allowlist |
| CORS_ALLOWED_ORIGINS | Comma-separated exact origins; default empty |
| LOG_LEVEL | Structured logging level; default INFO |
| OUTBOX_MAX_RETRIES | Per-event publishing attempt limit; default 10 |

The Compose file is development infrastructure, with all host ports bound to loopback. API and worker run as an unprivileged OS user and the database runtime role `organization_app` cannot create schemas, roles, or tables. A separate one-shot migrator owns schema changes. Local bootstrap uses a privileged PostgreSQL initialization/migration account and shares its password with the restricted runtime role for developer convenience only. Production must use separate migration/runtime secrets and a non-superuser schema owner, private networking, managed secrets, TLS for PostgreSQL/AMQP, TLS termination, backups, monitoring, and an appropriately configured gateway. Do not use development Compose as a production deployment manifest.

Production settings enforce HTTPS redirects, secure cookies, HSTS, clickjacking protection, restricted hosts/CORS and DEBUG=False. Configure trusted proxy behavior deliberately for your deployment; arbitrary forwarded TLS headers are not trusted by default. DRF throttling provides a basic per-process development limit; a distributed gateway rate limit is required for multi-worker production policy. No Redis dependency is introduced.

Structured logs contain request IDs, tenant/user/member IDs, path, method, status and duration. They omit request bodies and credentials. Valid bounded `X-Correlation-ID` values are preserved; other values are replaced. IDs flow into audit records and event envelopes.

## Event delivery and deferred scope

See [event contracts](../../docs/event-contracts.md) for exchanges, queues, delivery semantics and the generated JSON schema. An outbox event and audit row are mandatory writes in each domain command transaction. Publisher failure does not invalidate already committed domain data.

Phase 2 owns authentication, QR challenges, platform identity verification, devices and sessions using FastAPI. Messaging, realtime, media, notifications, Flutter, Next.js, calls and billing implementations are absent. Permission names for future billing/device services are contracts only.
