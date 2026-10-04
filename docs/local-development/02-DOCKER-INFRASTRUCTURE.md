Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Isolated Docker infrastructure
Compose file: docker-compose.local.yml. Project globalchat-local. PostgreSQL 16: host 5434 (5432/5433 already used on this machine); Redis 7: 6380 (6379 already used); RabbitMQ 4: 5672, management 15672. All ports bind loopback. Volumes persist.

```powershell
docker compose --env-file .local/compose.env -f docker-compose.local.yml ps
```
Expected: healthy postgres/redis/rabbitmq. YOU DO THIS MANUALLY: open http://localhost:15672, use local Rabbit credentials privately from .local/config.json; inspect queues, consumers and unacknowledged messages. Never paste credentials into reports.
