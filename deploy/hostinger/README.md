# GlobalChat on Hostinger VPS (Docker Compose)

Production runs on a **single Linux VPS** (e.g. Hostinger KVM 2). **AWS is used only for private S3** encrypted media objects. API HTTPS and realtime WSS terminate on **Caddy** on the VPS.

## Prerequisites

- Ubuntu 22.04+ (or similar), Docker Engine 24+ and Compose v2
- DNS `A`/`AAAA` for `API_DOMAIN` and `WS_DOMAIN` pointing at the VPS
- AWS account with a **private** media bucket and IAM user (see `infrastructure/aws/s3-media/README.md`)
- Generated RS256 keypair for Identity access tokens

## 1. Clone and configure

```bash
git clone <repo> /opt/globalchat
cd /opt/globalchat/deploy/hostinger
cp .env.example .env
# Edit .env: domains, passwords, JWT keys, S3 bucket/region, AWS keys (never commit .env)
```

Mount multiline PEM keys safely (recommended):

```bash
mkdir -p secrets
# Copy private/public PEM files, then in .env use file paths only if your orchestration supports it,
# or export ACCESS_TOKEN_PRIVATE_KEY / ACCESS_TOKEN_PUBLIC_KEY via a root-only env file sourced before compose.
```

URL-encode the Postgres password for compose:

```bash
python3 -c "import urllib.parse, os; print(urllib.parse.quote(os.environ['POSTGRES_PASSWORD']))"
# paste into POSTGRES_PASSWORD_URLENCODED
```

## 2. AWS S3 (media only)

1. Create bucket (SSE-S3, block public access, versioning optional).
2. Attach least-privilege policy from `infrastructure/aws/s3-media/iam-vps-media-policy.json` to an IAM **user** for the VPS.
3. Configure CORS `GET, HEAD, PUT` for your app origins; expose `ETag` for multipart (see `infrastructure/aws/s3-media/README.md`).
4. Set `AWS_REGION`, `MEDIA_S3_BUCKET`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` in `.env`.

Media flow: client encrypts locally → presigned PUT (ciphertext) → `POST /api/v1/media/{id}/complete` → E2EE message body. **No bucket keys or plaintext** on the API.

## 3. Start infrastructure

```bash
docker compose --env-file .env -f docker-compose.yml up -d postgres redis rabbitmq
docker compose --env-file .env -f docker-compose.yml ps
# wait until postgres/rabbit/redis healthy
```

## 4. Migrations (order)

```bash
chmod +x scripts/migrate-all.sh
./scripts/migrate-all.sh
```

Critical revisions for GlobalChat mobile E2EE:

| Service | Revision |
|---------|----------|
| identity-service | `0011_device_e2ee_keys` |
| messaging-service | `0005_message_e2ee_envelope` |

## 5. Start application stack

```bash
docker compose --env-file .env -f docker-compose.yml up -d --build
```

Caddy obtains TLS certificates automatically when `API_DOMAIN` / `WS_DOMAIN` resolve to this host.

## 6. Health verification

```bash
curl -fsS "https://${API_DOMAIN}/health/ready"
curl -fsS "http://localhost:8007/health/ready"   # from VPS shell via docker exec if needed
```

With a valid user token:

- `GET https://${API_DOMAIN}/api/v1/auth/me`
- `GET https://${API_DOMAIN}/api/v1/platform/services` (platform admin) — optional aggregate check

WebSocket (replace token):

`wss://${WS_DOMAIN}/api/v1/realtime?token=<access_token>`

## 7. Mobile / web clients

```bash
flutter run \
  --dart-define=API_BASE_URL=https://YOUR_API_DOMAIN \
  --dart-define=REALTIME_WSS_URL=wss://YOUR_WS_DOMAIN/api/v1/realtime
```

## Backups

- **Postgres:** snapshot `postgres_data` volume or `pg_dump` per logical database on a schedule; store off-VPS encrypted.
- **RabbitMQ / Redis:** optional; rebuild from outbox where possible. Prioritize Postgres.
- **S3:** enable versioning/lifecycle in AWS; application deletes objects on media delete API.

## Local development

Unchanged: `docker-compose.local.yml` + `python scripts/local/dev.py` on the workstation. Root `docker-compose.yml` remains a **partial dev** stack (host Postgres on `host.docker.internal`); do not use it as production.

## Rollout checklist

See `apps/mobile/globalchatapp/docs/STAGING-E2E-CHECKLIST.md` after deploy.

**Production readiness** requires your own smoke tests on this VPS — this repository does not validate a live Hostinger deployment.
