"""Transactional projection-backed consumer for Messaging's message.created.v1."""

from dataclasses import dataclass
from uuid import NAMESPACE_URL, UUID, uuid5

from app.db import SessionLocal
from app.repositories import (
    NotificationDeliveryRepository,
    NotificationRepository,
    OutboxRepository,
    PreferenceRepository,
    ProcessedEventRepository,
    ProjectionRepository,
    PushTokenRepository,
)

MESSAGE_CREATED_EVENT = "message.created.v1"
NOTIFICATION_CREATED_EVENT = "notification.created.v1"


class UnsupportedMessageEvent(ValueError):
    """A malformed or unsupported message contract that should be discarded."""


class MessageProjectionUnavailable(RuntimeError):
    """A required local projection has not arrived yet; delivery should be retried."""


@dataclass(frozen=True)
class MessageCreatedEvent:
    event_id: UUID
    organization_id: UUID
    conversation_id: UUID
    message_id: UUID
    sender_user_id: UUID
    sender_member_id: UUID
    correlation_id: str

    @classmethod
    def from_dict(cls, raw_event: dict):
        try:
            if raw_event["event_type"] != MESSAGE_CREATED_EVENT or raw_event["event_version"] != 1:
                raise UnsupportedMessageEvent("unsupported message event contract")
            payload = raw_event["payload"]
            if not isinstance(payload, dict):
                raise UnsupportedMessageEvent("message event payload must be an object")
            organization_id = UUID(str(raw_event["organization_id"]))
            payload_organization_id = UUID(str(payload["organization_id"]))
            if organization_id != payload_organization_id:
                raise UnsupportedMessageEvent("message event organization mismatch")
            return cls(
                event_id=UUID(str(raw_event["event_id"])),
                organization_id=organization_id,
                conversation_id=UUID(str(payload["conversation_id"])),
                message_id=UUID(str(payload["message_id"])),
                sender_user_id=UUID(str(payload["sender_user_id"])),
                sender_member_id=UUID(str(payload["sender_member_id"])),
                correlation_id=str(raw_event.get("correlation_id", "")),
            )
        except UnsupportedMessageEvent:
            raise
        except (KeyError, TypeError, ValueError) as exc:
            raise UnsupportedMessageEvent("malformed message event envelope") from exc


class MessageNotificationConsumer:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    async def consume(self, raw_event: dict) -> bool:
        event = MessageCreatedEvent.from_dict(raw_event)
        async with self.session_factory() as session:
            async with session.begin():
                processed_events = ProcessedEventRepository(session)
                if await processed_events.exists(event.event_id):
                    return False
                await self._create_notifications(session, event)
                await processed_events.add(
                    event.event_id, MESSAGE_CREATED_EVENT, event.organization_id
                )
        return True

    async def _create_notifications(self, session, event):
        projections = ProjectionRepository(session)
        conversation = await projections.get_conversation(
            event.organization_id, event.conversation_id
        )
        if conversation is None or conversation.status != "ACTIVE":
            raise MessageProjectionUnavailable(
                "active tenant conversation projection is unavailable"
            )

        notifications = NotificationRepository(session)
        deliveries = NotificationDeliveryRepository(session)
        preferences = PreferenceRepository(session)
        tokens = PushTokenRepository(session)
        outbox = OutboxRepository(session)
        members = await projections.active_conversation_members(
            event.organization_id, event.conversation_id
        )
        for conversation_member in members:
            if (
                conversation_member.member_id == event.sender_member_id
                or conversation_member.user_id == event.sender_user_id
            ):
                continue
            membership = await projections.get_membership(
                event.organization_id, conversation_member.member_id
            )
            if (
                membership is None
                or membership.status != "ACTIVE"
                or membership.user_id != conversation_member.user_id
            ):
                continue
            preference = await preferences.get(event.organization_id, conversation_member.member_id)
            push_enabled = preference is None or preference.push_enabled
            preview_mode = preference.preview if preference is not None else "FULL"
            notification = await notifications.get_by_dedupe_identity(
                event.organization_id,
                event.message_id,
                conversation_member.member_id,
                "MESSAGE",
            )
            if notification is None:
                notification = await notifications.create(
                    organization_id=event.organization_id,
                    conversation_id=event.conversation_id,
                    message_id=event.message_id,
                    recipient_user_id=conversation_member.user_id,
                    recipient_member_id=conversation_member.member_id,
                    notification_type="MESSAGE",
                    title=None,
                    body=None,
                    preview_mode=preview_mode,
                )
            if push_enabled:
                existing_tokens = await deliveries.token_ids_for_notification(
                    event.organization_id, notification.id
                )
                active_tokens = await tokens.active_for_user(
                    event.organization_id, conversation_member.user_id
                )
                missing_tokens = [
                    token for token in active_tokens if token.id not in existing_tokens
                ]
                if missing_tokens:
                    await deliveries.create_many(
                        [
                            {
                                "organization_id": event.organization_id,
                                "notification_id": notification.id,
                                "device_push_token_id": token.id,
                                "device_id": token.device_id,
                                "provider": token.provider,
                                "status": "PENDING",
                                "attempt_count": 0,
                                "next_attempt_at": None,
                            }
                            for token in missing_tokens
                        ]
                    )
            outbox_event_id = uuid5(
                NAMESPACE_URL,
                f"{NOTIFICATION_CREATED_EVENT}:{event.organization_id}:{notification.id}",
            )
            if await outbox.get_by_event_id(outbox_event_id) is None:
                await outbox.add(
                    event_id=outbox_event_id,
                    organization_id=event.organization_id,
                    event_type=NOTIFICATION_CREATED_EVENT,
                    status="PENDING",
                    payload={
                        "notification_id": str(notification.id),
                        "organization_id": str(event.organization_id),
                        "conversation_id": str(event.conversation_id),
                        "message_id": str(event.message_id),
                        "recipient_user_id": str(conversation_member.user_id),
                        "recipient_member_id": str(conversation_member.member_id),
                        "preview_mode": notification.preview_mode,
                    },
                )
