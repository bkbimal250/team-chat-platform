Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# RabbitMQ testing
`python scripts/local/dev.py tests` includes Organization test_real_broker_confirm_delivery_and_manual_ack; real broker publisher confirmation, event envelope and manual ACK are exercised.

YOU DO THIS MANUALLY: http://localhost:15672 -> Exchanges/Queues. Expected queues include identity.membership, user.identity, conversation.membership, messaging.authorization, media.references, notification.projections, notification.message-created, realtime.events and local.events.audit. Organization has archive/dead queues. Normal processing queues should drain; audit/archive queues intentionally retain events.

No universal DLQ exists: several current consumers NACK/requeue indefinitely; malformed poison events need operator investigation. Do not claim dead-letter behavior for those queues. Outbox implementations have service-specific retry behavior. Exact runner commands are defined in scripts/local/dev.py WORKERS; startup runs all fifteen workers.
