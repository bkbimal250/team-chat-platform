Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Event flows
Identity outbox -> organization.events identity.# -> User consumer -> user.events -> Conversation block projection and Notification global user projection. Organization outbox -> organization.events member.# -> Identity/User/Conversation/Notification. Conversation outbox -> organization.events conversation.# -> Messaging/Realtime/Notification. Messaging outbox -> messaging.events message.# -> Conversation summaries, Realtime, Media references, Notification pipeline. Media outbox -> media.events -> Messaging ready-media projection. Notification outbox -> notification.events.

Manual ACK occurs after commit; failure NACK/requeue. Outbox publisher confirmation precedes PUBLISHED. Domain consumer idempotency uses processed_events; realtime delivery dedupe uses Redis NX/EX. Local archive local.events.audit is bounded to 1000 messages and ensures observable domain publications even when no feature consumer subscribes. It is not application processing.
