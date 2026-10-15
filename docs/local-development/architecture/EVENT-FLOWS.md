Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Event flows

## Local worker commands

Run commands with the owning service virtual environment, working directory and private configuration; `scripts/local/dev.py start` supplies these together. Do not launch a second copy over an existing worker.

| Service | Outbox | Consumer / delivery |
|---|---|---|
| Organization | `python manage.py publish_outbox` | Domain publisher only |
| Identity | `python -m app.events.run_worker` | `python -m app.consumer_runner` |
| User | `python -m app.outbox_runner` | `python -m app.consumer_runner` |
| Conversation | `python -m app.outbox_runner` | `python -m app.consumer_runner` |
| Messaging | `python -m app.outbox_runner` | `python -m app.consumer_runner` |
| Media | `python -m app.outbox_runner` | `python -m app.consumer_runner` |
| Notification | `python -m app.outbox_runner` | `python -m app.consumer_runner`; `python -m app.delivery_worker` |
| Realtime | None | `python -m app.consumer_runner` |
| Gateway | None | None |

There are fifteen worker processes, separate from nine HTTP APIs. Inspect queues through [RabbitMQ testing](../testing/RABBITMQ-TESTING.md). Literal event names and source-linked handlers are included in each service reference; an event name in a test is not proof that every consumer supports it.
Identity outbox -> organization.events identity.# -> User consumer -> user.events -> Conversation block projection and Notification global user projection. Organization outbox -> organization.events member.# -> Identity/User/Conversation/Notification. Conversation outbox -> organization.events conversation.# -> Messaging/Realtime/Notification. Messaging outbox -> messaging.events message.# -> Conversation summaries, Realtime, Media references, Notification pipeline. Media outbox -> media.events -> Messaging ready-media projection. Notification outbox -> notification.events.

Manual ACK occurs after commit; failure NACK/requeue. Outbox publisher confirmation precedes PUBLISHED. Domain consumer idempotency uses processed_events; realtime delivery dedupe uses Redis NX/EX. Local archive local.events.audit is bounded to 1000 messages and ensures observable domain publications even when no feature consumer subscribes. It is not application processing.


## Secure employee onboarding (2026-10-05)

Employee onboarding adds no parallel OTP/event bus. Identity VERIFIED intent -> idempotent User profile -> atomic Organization member/role/branch/team plus audit/outbox -> Identity activation/normal session. Existing member.*.v2 and user/identity event consumers retain ProcessedEvent/idempotent redelivery. Tokens/phones/OTP/email are absent from events. A newly-created conversation may require its Messaging authorization event to arrive before sending; never bypass that boundary.
