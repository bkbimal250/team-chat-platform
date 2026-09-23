# Team Chat Platform — Phase 1

The Organization Service is implemented in [services/organization-service](services/organization-service/README.md). Other service directories are reserved for later phases.

Start with the [service README](services/organization-service/README.md), [Phase 1 implementation report](docs/phase-1-report.md), and [event contracts](docs/event-contracts.md).

```powershell
Copy-Item .env.example .env
# Replace all three placeholder secrets in .env before starting.
docker compose up -d --build
docker compose exec organization-service python manage.py provision_organization --name "Example" --slug example --owner-name "Owner" --owner-user-id "11111111-1111-4111-8111-111111111111"
```

An untracked `.env` with generated local secrets may already exist in this workspace; preserve it when continuing the current installation.

Development Swagger: http://localhost:8000/api/docs/ • Admin: http://localhost:8000/admin/

Phase 1 is a backend foundation. The development `X-Dev-Member-ID` adapter is deliberately unsafe and must never be exposed publicly. Production product endpoints remain closed until Phase 2 supplies verified identity context. Django operator login is separate.
