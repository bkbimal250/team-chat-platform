# Phase 1 implementation report

Phase 1 provides the multi-tenant Organization Service at `services/organization-service`. It is a Django/DRF service for organizations, branches, teams, organization members, role-based authorization, invitations, audits and domain events. It contains no end-user authentication, QR/device/session logic, messages, media, web sockets, clients, billing, or calling.

## Structure

```text
services/organization-service/
  apps/{organizations,branches,teams,members,roles,invitations,audit}/
  common/{authorization,context,services,selectors,middleware}/
  config/settings/{base,local,production}.py
  events/{schemas,publishers,outbox}/
  tests/{security,integration}/
  Dockerfile  pyproject.toml  README.md
docker-compose.yml
docs/{phase-1-report,event-contracts}.md
```

## Models and database integrity

The service models `Organization`, `OrganizationSettings`, `Branch`, `Team`, `Member`, `TeamMembership`, `BranchMembership`, `Permission`, `Role`, `RolePermission`, `RoleAssignment`, `Invitation`, `AuditLog`, and `OutboxEvent`. All external identifiers are UUID4 generated through a small `new_id` seam, so a future UUID strategy migration has one call site.

Tenant rows include `organization_id`. PostgreSQL protects relationships with composite foreign keys `(organization_id, referenced_id)`, including raw ORM/bulk writes. Partial unique indexes enforce branch code within a tenant, active membership uniqueness, and exactly one active primary branch per member. `Member.user_id` and employee code are each unique only inside a tenant when set. Team names are case-sensitive unique inside a tenant, including inactive rows. Status choices are protected by application choices and database CHECK constraints. Tenant ownership is immutable through a database trigger. Audit rows are append-only through a database trigger.

## API and security

Every public operation begins at `/api/v1/`; complete endpoint inventory, filters and payloads are in the [service README](../services/organization-service/README.md). `GET/PATCH /api/v1/organizations/current/` and settings/lifecycle operations operate only on the tenant from `TenantContext`. Tenant-safe query selectors back all API reads, so foreign-tenant resources return 404. Domain services validate every indirect tenant-owned reference before writing and are backed by the composite foreign keys.

Roles hold stable global permission codes through tenant-scoped assignments. OWNER, ADMIN, MANAGER, MEMBER and custom roles are supported. Permission checks are centralized, and commands recheck current permissions while holding the tenant row lock. Role delegation cannot grant permissions the actor does not hold; only an owner may grant ownership; the final active owner cannot be removed, suspended or lose owner assignment.

`X-Dev-Member-ID` is a deliberately temporary local test adapter. It resolves an active database member, never trusts client-supplied organization or permissions, and is disabled by default. Production settings reject it and fail closed pending a Phase 2 verified identity adapter. Django admin users are separate operator identities.

## Events and outbox

Each explicit command writes its domain row, append-only audit record, and typed `OutboxEvent` within the same transaction. The RabbitMQ topic exchange is `organization.events`; events use routing keys such as `team.created.v1`, persistent messages, mandatory routing, durable topology and publisher confirms. The worker locks eligible rows with `SKIP LOCKED`, uses exponential retry, retains the same `event_id`, and marks exhausted events FAILED for explicit operator requeue.

Delivery is at-least-once: a crash after broker confirmation but before the database commit can duplicate an event. Consumers must deduplicate on event ID and acknowledge only after their own database transaction commits. [Event contracts](event-contracts.md) documents the envelope, queue topology, retry and consumer requirements. The machine-readable envelope is [envelope.v1.json](../services/organization-service/events/schemas/envelope.v1.json).

## Deployment and operation

`docker-compose.yml` starts PostgreSQL, RabbitMQ, a one-shot migration job, the API, and the outbox worker. Docker binds database and broker ports to loopback only. The app/worker image uses a non-root Linux user; a runtime database role is separate from the migration account. Production needs separate migration/runtime credentials, private networking, TLS, managed secrets, backups, alerting and gateway rate limits.

Required configuration is `SECRET_KEY`, `DATABASE_URL`, `RABBITMQ_URL`, `ALLOWED_HOSTS`, `ENVIRONMENT`, and service-specific logging/CORS/outbox settings. The root and service `.env.example` files document all values.

Swagger: `http://localhost:8000/api/docs/`. Redoc: `http://localhost:8000/api/redoc/`. Schema: `http://localhost:8000/api/schema/`. Django Admin: `http://localhost:8000/admin/`. Health: `/health/live` and `/health/ready`.

## Validation completed

On 2026-09-22:

* `python manage.py check` passed.
* `makemigrations --check --dry-run` passed.
* `ruff format` and `ruff check` passed.
* drf-spectacular validation passed with no warnings.
* `pytest -q` passed: **31 tests**, including tenant isolation, API, permission, lifecycle, real PostgreSQL constraints, transaction rollback, concurrency, outbox retry and live RabbitMQ confirm/ack coverage.
* Docker image build, migrations, PostgreSQL readiness, RabbitMQ connection, service readiness, Swagger schema, and Django Admin all succeeded.

The test suite completed without warnings.

## Known limitations and Phase 2 boundary

Provisioning, member identity linking, invitation acceptance and tenant recovery are trusted operator/domain commands in this phase. They do not authenticate people or generate invitation/QR credentials. No distributed rate limiter, PostgreSQL row-level security, metrics endpoint, or archival/retention policy is included. The archive queue is a durable operational record, so capacity and retention need production planning.

Phase 2 will add FastAPI identity/authentication, verified claims, QR challenges, devices and sessions. Messaging, conversations, real-time delivery, media/S3, notifications, Flutter/Next.js clients, billing and all calling/WebRTC work remain intentionally deferred.
