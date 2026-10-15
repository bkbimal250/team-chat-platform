# Deployment architecture

| Layer | Where |
|-------|--------|
| API gateway, services, workers, Postgres, Redis, RabbitMQ, Caddy (HTTPS + WSS) | **Hostinger VPS** — `deploy/hostinger/docker-compose.yml` |
| Encrypted media objects | **AWS S3** (private bucket, presigned PUT/GET, IAM user on VPS) |
| Local dev | `docker-compose.local.yml` + `scripts/local/dev.py`; root `docker-compose.yml` is partial dev-only |

Operator guide: [`deploy/hostinger/README.md`](../../deploy/hostinger/README.md). S3 setup: [`infrastructure/aws/s3-media/README.md`](../../infrastructure/aws/s3-media/README.md).

Only Caddy exposes ports 80/443 on the VPS. Do not publish Postgres, Redis, RabbitMQ management, or service ports publicly. Never commit `.env` or AWS keys.
