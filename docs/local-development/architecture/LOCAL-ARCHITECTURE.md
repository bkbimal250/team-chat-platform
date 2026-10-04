Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Architecture
Browser -> Gateway 8008 -> domain APIs. WebSocket -> Realtime 8007. PostgreSQL domain transaction + outbox -> RabbitMQ -> idempotent projections / Realtime -> shared Redis routing -> recipient sockets. Signed local media bytes go directly to Media 8005, not through Gateway. Production S3 adapter remains intact; local filesystem is development-only and metadata remains durable PostgreSQL state.
