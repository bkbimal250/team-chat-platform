Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Implementation status
Working real local baseline: Docker infrastructure, seven migrated domain databases, nine APIs, fifteen workers, explicit invite-only seed, Gateway routing, text/realtime/typing/receipts, private local attachments. Source repairs address initial migration duplication, durable User outbox state, membership contract compatibility, Windows signal handling, persistent consumer event loops, async Redis consumer wiring, Pika thread ownership, first receipt counters and group rejoin.

API references are generated from actual running OpenAPI. Routes marked PARTIAL in master inventory are schema-verified but not individually mutation-tested. Do not treat documentation existence as execution proof. Full live result and regression counts are in TEST-RESULTS.md.
