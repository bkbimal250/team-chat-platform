from uuid import NAMESPACE_URL, UUID, uuid5

from app.notification_copy import push_copy
from app.repositories import (
    BlockRepository,
    ConversationMuteRepository,
    NotificationDeliveryRepository,
    NotificationRepository,
    OutboxRepository,
    PreferenceRepository,
    ProjectionRepository,
    PushTokenRepository,
)

NOTIFICATION_CREATED_EVENT = "notification.created.v1"
INACTIVE_MEMBERSHIP = frozenset({"LEFT", "REMOVED", "SUSPENDED"})


class NotificationFanout:
    def __init__(self, session):
        self.session = session
        self.projections = ProjectionRepository(session)
        self.notifications = NotificationRepository(session)
        self.deliveries = NotificationDeliveryRepository(session)
        self.preferences = PreferenceRepository(session)
        self.tokens = PushTokenRepository(session)
        self.outbox = OutboxRepository(session)
        self.mutes = ConversationMuteRepository(session)
        self.blocks = BlockRepository(session)

    async def notify_member(
        self,
        *,
        organization_id: UUID | None,
        conversation_id: UUID | None,
        message_id: UUID | None,
        recipient_user_id: UUID,
        recipient_member_id: UUID,
        notification_type: str,
        sender_user_id: UUID | None,
        sender_label: str | None,
        is_group: bool,
        dedupe_message_id: UUID | None,
    ):
        if sender_user_id and await self.blocks.is_blocked_either_way(
            sender_user_id, recipient_user_id
        ):
            return None
        if organization_id is not None:
            membership = await self.projections.get_membership(organization_id, recipient_member_id)
            if membership is None or membership.status in INACTIVE_MEMBERSHIP:
                return None
        if conversation_id and await self.mutes.is_muted(
            organization_id, conversation_id, recipient_member_id
        ):
            return None
        preference = await self.preferences.get(organization_id, recipient_member_id)
        preview_mode = preference.preview if preference is not None else "FULL"
        if preference is not None:
            if notification_type in {"MESSAGE", "MENTION"} and not preference.message_notifications:
                return None
            if notification_type == "GROUP" and not preference.group_notifications:
                return None
            if notification_type in {"MESSAGE", "MENTION"} and is_group and not preference.group_notifications:
                return None
        push_enabled = preference is None or preference.push_enabled
        title, body = push_copy(notification_type, preview_mode, sender_label)
        notification = await self.notifications.get_by_dedupe_identity(
            organization_id,
            dedupe_message_id or message_id,
            recipient_member_id,
            notification_type,
        )
        if notification is None:
            notification = await self.notifications.create(
                organization_id=organization_id,
                conversation_id=conversation_id,
                message_id=dedupe_message_id or message_id,
                recipient_user_id=recipient_user_id,
                recipient_member_id=recipient_member_id,
                notification_type=notification_type,
                title=title,
                body=body,
                preview_mode=preview_mode,
            )
        if push_enabled:
            existing = await self.deliveries.token_ids_for_notification(
                organization_id, notification.id
            )
            for token in await self.tokens.active_for_user(organization_id, recipient_user_id):
                if token.id in existing:
                    continue
                await self.deliveries.create(
                    organization_id=organization_id,
                    notification_id=notification.id,
                    device_push_token_id=token.id,
                    device_id=token.device_id,
                    provider=token.provider,
                    status="PENDING",
                    attempt_count=0,
                    next_attempt_at=None,
                )
        event_id = uuid5(
            NAMESPACE_URL,
            f"{NOTIFICATION_CREATED_EVENT}:{organization_id}:{notification.id}",
        )
        if await self.outbox.get_by_event_id(event_id) is None:
            await self.outbox.add(
                event_id=event_id,
                organization_id=organization_id,
                event_type=NOTIFICATION_CREATED_EVENT,
                status="PENDING",
                payload={
                    "notification_id": str(notification.id),
                    "organization_id": str(organization_id) if organization_id else None,
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "message_id": str(message_id) if message_id else None,
                    "recipient_user_id": str(recipient_user_id),
                    "recipient_member_id": str(recipient_member_id),
                    "notification_type": notification_type,
                    "preview_mode": notification.preview_mode,
                    "scope": "personal" if organization_id is None else "company",
                },
            )
        return notification
