# GlobalChat cross-service event contract matrix

Authoritative membership lifecycle uses **`member.*.v2`** on exchange **`organization.events`** with `event_version: 2` and `MembershipPayload`. Legacy `member.*.v1` is not emitted for new member writes.

`organization_id: null` means **personal scope** (not global/public). Workspace events require a non-null `organization_id`.

| Exchange | Routing key | Version | Producer | Consumers (queues / services) | Required payload | IDs |
|---|---|---:|---|---|---|---|
| `organization.events` | `identity.created.v1` | 1 | identity-service | user.identity (`identity.#`), notification.projections (`identity.#`) | `identity_id`, optional `phone_e164` | `identity_id` = permanent identity |
| `organization.events` | `invitation.created.v1` | 1 | organization-service | notification.org-events | `invitation_id`, `status`, optional `recipient_phone_e164`, `recipient_email` | No member until accept |
| `organization.events` | `member.*.v2` | 2 | organization-service | identity.membership, user.identity, conversation/messaging/media/realtime/notification consumers | `MembershipPayload`: `member_id`, `user_id`, `identity_id`, `status`, `participant_kind` | `user_id`/`identity_id` = platform user; `member_id` = org member row |
| `organization.events` | `conversation.*.v1` | 1 | conversation-service | messaging.authorization, notification.projections, realtime.events | conversation + member fields per event | `conversation_id`, `member_id`, `user_id` |
| `user.events` | `user.created.v1` | 1 | user-service | notification.projections | `user_id`, `identity_id` | Links identity → user profile |
| `user.events` | `user.blocked.v1` / `user.unblocked.v1` | 1 | user-service | messaging.authorization, conversation.membership, notification.projections | blocker/blocked user ids | Privacy |
| `messaging.events` | `message.created.v1` | 1 | messaging-service | realtime.events, notification.message-created | `message_id`, `conversation_id`, `sender_user_id`, `sender_member_id`, optional `mentioned_member_ids[]`, nullable `organization_id` | Mention list uses **member_id** |
| `messaging.events` | `message.reaction_added.v1` | 1 | messaging-service | realtime.events, notification.message-created | message fields + `reactor_member_id`, `reactor_user_id`, `reaction` | Reactor ≠ message author |
| `media.events` | `media.ready.v1` / `media.deleted.v1` | 1 | media-service | messaging.authorization | `media_id`, `conversation_id`, `uploader_member_id`, metadata | Tenant via `organization_id` |
| `notification.events` | `notification.created.v1` | 1 | notification-service | (downstream delivery worker) | `notification_id`, recipient ids, scope | Personal: `organization_id` null |

All consumers use **processed-event idempotency** (outbox or `processed_events` table) and at-least-once RabbitMQ delivery.
