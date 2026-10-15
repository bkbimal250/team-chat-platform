Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Service ports
| Service | Host port | Schema path |
|---|---:|---|
| Organization | 8000 | `/api/schema/` |
| Identity | 8001 | `/api/schema/` |
| User | 8002 | `/openapi.json` |
| Conversation | 8003 | `/api/schema/` |
| Messaging | 8004 | `/openapi.json` |
| Media | 8005 | `/openapi.json` |
| Notification | 8006 | `/openapi.json` |
| Realtime | 8007 | `/openapi.json` |
| Gateway | 8008 | `/openapi.json` |
| Admin frontend | 3000 | n/a |
| Main web frontend, alongside admin | 3001 | n/a |

All nine APIs expose `/health/live` and `/health/ready`. Windows APIs use loopback; infrastructure runs in Docker. PostgreSQL host 5434 maps to container 5432; Redis host 6380 maps to 6379, database 0; RabbitMQ 5672 and management UI 15672 use vhost `/`. These runner ports override standalone service example defaults. See `scripts/local/dev.py` and `docker-compose.local.yml` at repository root.

Platform service readiness is aggregated only by Gateway at `/api/v1/platform/services` after Identity validates `platform.services.read`. It is not a public operational endpoint and does not return configuration or credentials.
