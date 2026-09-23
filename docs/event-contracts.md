# Organization domain events, version 1

Producer: `organization-service`. Durable topic exchange: `organization.events`. Routing key equals event type. Durable local archive queue: `organization.events.archive`, bound with `#`. Dead-letter topic exchange: `organization.dead`; durable queue: `organization.events.dead`, bound with `#`. The archive queue dead-letters rejected messages to this exchange.

The typed source contract is `events/schemas/__init__.py`, with generated JSON Schema in `services/organization-service/events/schemas/envelope.v1.json`. The event-type registry rejects unregistered names. Version changes require a new contract/routing key rather than silently changing v1 semantics.

```json
{
  "event_id": "11111111-1111-4111-8111-111111111111",
  "event_type": "team.created.v1",
  "event_version": 1,
  "occurred_at": "2026-09-22T12:00:00Z",
  "producer": "organization-service",
  "organization_id": "22222222-2222-4222-8222-222222222222",
  "aggregate_id": "33333333-3333-4333-8333-333333333333",
  "correlation_id": "gateway-request-123",
  "payload": {
    "resource_id": "33333333-3333-4333-8333-333333333333",
    "changed_fields": ["name"],
    "status": "ACTIVE"
  }
}
```

Payloads are deliberately minimal change notifications. `resource_id` is the aggregate ID; `changed_fields` identifies changed model/input field names (not values); `status` is the current resource status or null for models without lifecycle status. Consumers requiring a detailed projection must use an authorized service API. No credentials, invitation secrets, personal profile snapshots or QR tokens are included. `occurred_at` is the outbox insertion time, preserved across retries.

| Aggregate | Actions (append `.v1` to `aggregate.action`) |
|---|---|
| organization | created, updated, suspended, disabled, deleted |
| organization_settings | updated |
| branch | created, updated, disabled, deleted |
| team | created, updated, disabled, deleted |
| member | created, updated, activated, suspended, left, removed, role_changed |
| invitation | created, accepted, revoked, expired |
| team_membership | created, left |
| branch_membership | created, left, updated |
| role | created, updated (reserved for future custom permission-set edits) |

The worker locks one eligible outbox row with `SELECT FOR UPDATE SKIP LOCKED`, marks PROCESSING inside the transaction, publishes a persistent message with `mandatory=True`, waits for publisher confirmation, then commits PUBLISHED. Network/blocking timeouts bound the lock duration. A worker crash rolls the transaction back, so PROCESSING cannot be stranded in committed state. A crash after RabbitMQ accepts the event and before the database commit can redeliver it with the same `event_id`: this is **at-least-once**, not exactly-once.

Failure increments `retry_count`, records only the exception class and schedules retry after `min(2^retry_count, 3600)` seconds. At 10 failures (configurable) the row becomes FAILED and needs operator investigation/requeue. Connection establishment failures leave rows PENDING; the worker reconnects every two seconds. Event ordering across parallel workers is not guaranteed. Treat events as invalidations or use version-aware reconciliation when building future projections.

Every future consuming service should own a separate durable queue and DLQ, acknowledge only after a local transaction commits, and enforce unique `(consumer, event_id)` in its inbox. Redelivered already-applied events should be acknowledged without applying again. Transient consumer errors require bounded retries/backoff; permanent/exhausted failures should `basic_nack(requeue=False)` into the DLQ. Do not blindly requeue poison messages. No product consumer service is implemented in Phase 1; integration tests prove explicit acknowledgements and dead-letter behavior against the live broker.

Publisher docs: [Pika mandatory delivery and confirms](https://pika.readthedocs.io/en/stable/examples/blocking_publish_mandatory.html). Tenant constraint design uses [Django constraints](https://docs.djangoproject.com/en/5.2/ref/models/constraints/) plus explicit PostgreSQL composite foreign keys.
