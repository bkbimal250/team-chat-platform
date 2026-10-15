Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Windows setup
Prerequisites: Docker Desktop, Python 3.12/service virtual environments, Node.js/npm. Existing service pyproject.toml files define dependencies. With uv: `uv sync --project services/identity-service --group dev` (repeat for each service). Realtime now requires httpx; its uv.lock includes this dependency. Startup prepares a bounded local broker archive and waits up to 60 seconds for API readiness.

Run from repository root in PowerShell:
```powershell
python scripts/local/dev.py prepare
python scripts/local/dev.py infra
python scripts/local/dev.py migrate
python scripts/local/dev.py start
python scripts/local/dev.py seed
python scripts/local/dev.py health
```
Expected: three healthy infrastructure containers, seven migration heads, nine APIs live/ready 200, fifteen workers. Credentials/keys generated locally under ignored .local/. Do not commit/share that directory. Do not replace existing private .env files.

Frontend:
```powershell
cd apps/web/web-chat-app
npm ci
# .env.local: NEXT_PUBLIC_API_URL=http://localhost:8008
# .env.local: NEXT_PUBLIC_WS_URL=ws://localhost:8007
npm run dev -- --hostname 127.0.0.1
```
When admin already occupies port 3000, run main web with `npm run dev -- --hostname 127.0.0.1 --port 3001`; open http://localhost:3001. Admin runs from `apps/admin-web/admin-webchat-app` on port 3000 with `NEXT_PUBLIC_API_BASE_URL=http://localhost:8008`. For backend restart: `python scripts/local/dev.py restart`. Stop only owned application processes: `python scripts/local/dev.py stop`. Infrastructure stop preserves volumes: `docker compose --env-file .local/compose.env -f docker-compose.local.yml stop`. Never use down -v for routine development.

The managed local runner retains DevelopmentOTPProvider configuration but disables phone OTP and enables email/password. A separately started Identity process using a private Vonage `.env` can send real SMS; do not assume the provider from APP_ENV alone. Use the [ordered manual tests](manual-testing/README.md) after readiness passes.
