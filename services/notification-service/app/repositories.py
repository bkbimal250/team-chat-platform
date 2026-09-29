from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.dialects.postgresql import insert

from app.models import (
    ConversationMemberProjection,
    ConversationProjection,
    DevicePushToken,
    GlobalUserProjection,
    MembershipProjection,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    OutboxEvent,
    ProcessedEvent,
    UserProjection,
)


class PushTokenRepository:
    def __init__(self, session):
        self.session = session

    async def upsert_current_device(self, principal, request):
        row = (
            await self.session.execute(
                select(DevicePushToken).where(
                    DevicePushToken.organization_id == principal.organization_id,
                    DevicePushToken.device_id == principal.device_id,
                    DevicePushToken.provider == request.provider,
                )
            )
        ).scalar_one_or_none()
        if row:
            row.platform, row.token, row.enabled = request.platform, request.push_token, True
            return row
        row = DevicePushToken(
            organization_id=principal.organization_id,
            user_id=principal.user_id,
            member_id=principal.member_id,
            device_id=principal.device_id,
            platform=request.platform,
            provider=request.provider,
            token=request.push_token,
        )
        self.session.add(row)
        await self.session.flush()
        return row

    async def disable_current_device(self, principal):
        rows = (
            await self.session.execute(
                select(DevicePushToken).where(
                    DevicePushToken.organization_id == principal.organization_id,
                    DevicePushToken.device_id == principal.device_id,
                )
            )
        ).scalars()
        for row in rows:
            row.enabled = False

    async def active_for_user(self, organization_id, user_id):
        return list(
            (
                await self.session.execute(
                    select(DevicePushToken).where(
                        DevicePushToken.organization_id == organization_id,
                        DevicePushToken.user_id == user_id,
                        DevicePushToken.enabled.is_(True),
                    )
                )
            ).scalars()
        )

    async def get_by_id(self, organization_id, token_id):
        return (
            await self.session.execute(
                select(DevicePushToken).where(
                    DevicePushToken.organization_id == organization_id,
                    DevicePushToken.id == token_id,
                )
            )
        ).scalar_one_or_none()

    async def disable_by_id(self, organization_id, token_id):
        token = await self.get_by_id(organization_id, token_id)
        if token is not None:
            token.enabled = False
        return token


class PreferenceRepository:
    def __init__(self, session):
        self.session = session

    async def get_or_create(self, principal):
        row = await self.get(principal.organization_id, principal.member_id)
        return row or await self.upsert(principal.organization_id, principal.member_id)

    async def get(self, organization_id, member_id):
        return (
            await self.session.execute(
                select(NotificationPreference).where(
                    NotificationPreference.organization_id == organization_id,
                    NotificationPreference.member_id == member_id,
                )
            )
        ).scalar_one_or_none()

    async def upsert(self, organization_id, member_id, *, push_enabled=True, preview="FULL"):
        statement = insert(NotificationPreference).values(
            organization_id=organization_id,
            member_id=member_id,
            push_enabled=push_enabled,
            preview=preview,
        )
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=("organization_id", "member_id"),
                set_={
                    "push_enabled": push_enabled,
                    "preview": preview,
                    "updated_at": func.now(),
                },
            )
        )
        await self.session.flush()
        return await self.get(organization_id, member_id)

    async def get_for_member(self, organization_id, member_id):
        return await self.get(organization_id, member_id)


class NotificationRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, **values):
        row = Notification(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_id(self, organization_id: UUID, notification_id: UUID):
        return (
            await self.session.execute(
                select(Notification).where(
                    Notification.organization_id == organization_id,
                    Notification.id == notification_id,
                )
            )
        ).scalar_one_or_none()

    async def get_by_dedupe_identity(
        self, organization_id, message_id, recipient_member_id, notification_type
    ):
        return (
            await self.session.execute(
                select(Notification).where(
                    Notification.organization_id == organization_id,
                    Notification.message_id == message_id,
                    Notification.recipient_member_id == recipient_member_id,
                    Notification.notification_type == notification_type,
                )
            )
        ).scalar_one_or_none()


class NotificationDeliveryRepository:
    def __init__(self, session):
        self.session = session

    async def create(self, **values):
        row = NotificationDelivery(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def create_many(self, deliveries):
        rows = [NotificationDelivery(**values) for values in deliveries]
        self.session.add_all(rows)
        await self.session.flush()
        return rows

    async def token_ids_for_notification(self, organization_id, notification_id):
        return set(
            (
                await self.session.execute(
                    select(NotificationDelivery.device_push_token_id).where(
                        NotificationDelivery.organization_id == organization_id,
                        NotificationDelivery.notification_id == notification_id,
                    )
                )
            ).scalars()
        )

    async def get_by_id(self, organization_id, delivery_id):
        return (
            await self.session.execute(
                select(NotificationDelivery).where(
                    NotificationDelivery.organization_id == organization_id,
                    NotificationDelivery.id == delivery_id,
                )
            )
        ).scalar_one_or_none()

    async def claim_batch(self, now, stale_cutoff, limit):
        rows = list(
            (await self.session.execute(self.claim_query(now, stale_cutoff, limit))).scalars()
        )
        for row in rows:
            row.status = "SENDING"
            row.claimed_at = now
            row.last_error = None
        await self.session.flush()
        return rows

    def claim_query(self, now, stale_cutoff, limit):
        return (
            select(NotificationDelivery)
            .where(
                or_(
                    NotificationDelivery.status == "PENDING",
                    and_(
                        NotificationDelivery.status == "RETRY_PENDING",
                        NotificationDelivery.next_attempt_at <= now,
                    ),
                    and_(
                        NotificationDelivery.status == "SENDING",
                        NotificationDelivery.claimed_at <= stale_cutoff,
                    ),
                )
            )
            .order_by(NotificationDelivery.next_attempt_at, NotificationDelivery.id)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )

    def claimable_query(self, organization_id, limit=100):
        return (
            select(NotificationDelivery)
            .where(
                NotificationDelivery.organization_id == organization_id,
                NotificationDelivery.status.in_(("PENDING", "RETRY_PENDING")),
            )
            .order_by(NotificationDelivery.next_attempt_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )


class ProjectionRepository:
    def __init__(self, session):
        self.session = session

    async def _upsert(self, model, identity, values):
        statement = insert(model).values(**values)
        update = {key: value for key, value in values.items() if key not in identity}
        await self.session.execute(
            statement.on_conflict_do_update(index_elements=identity, set_=update)
        )
        return await self._get_by(model, {key: values[key] for key in identity})

    async def _get_by(self, model, values):
        return (await self.session.execute(select(model).filter_by(**values))).scalar_one_or_none()

    async def upsert_user(self, **values):
        return await self._upsert(UserProjection, ("organization_id", "user_id"), values)

    async def upsert_membership(self, **values):
        return await self._upsert(MembershipProjection, ("organization_id", "member_id"), values)

    async def upsert_conversation(self, **values):
        return await self._upsert(
            ConversationProjection, ("organization_id", "conversation_id"), values
        )

    async def upsert_conversation_member(self, **values):
        return await self._upsert(
            ConversationMemberProjection,
            ("organization_id", "conversation_id", "member_id"),
            values,
        )

    async def get_conversation(self, organization_id, conversation_id):
        return await self._get_by(
            ConversationProjection,
            {"organization_id": organization_id, "conversation_id": conversation_id},
        )

    async def get_user(self, organization_id, user_id):
        return await self._get_by(
            UserProjection, {"organization_id": organization_id, "user_id": user_id}
        )

    async def memberships_for_user(self, user_id):
        return list(
            (
                await self.session.execute(
                    select(MembershipProjection).where(MembershipProjection.user_id == user_id)
                )
            ).scalars()
        )

    async def get_membership(self, organization_id, member_id):
        return await self._get_by(
            MembershipProjection, {"organization_id": organization_id, "member_id": member_id}
        )

    async def active_memberships(self, organization_id):
        return list(
            (
                await self.session.execute(
                    select(MembershipProjection).where(
                        MembershipProjection.organization_id == organization_id,
                        MembershipProjection.status == "ACTIVE",
                    )
                )
            ).scalars()
        )

    async def get_conversation_member(self, organization_id, conversation_id, member_id):
        return await self._get_by(
            ConversationMemberProjection,
            {
                "organization_id": organization_id,
                "conversation_id": conversation_id,
                "member_id": member_id,
            },
        )

    async def active_conversation_members(self, organization_id, conversation_id):
        return list(
            (
                await self.session.execute(
                    select(ConversationMemberProjection).where(
                        ConversationMemberProjection.organization_id == organization_id,
                        ConversationMemberProjection.conversation_id == conversation_id,
                        ConversationMemberProjection.status == "ACTIVE",
                    )
                )
            ).scalars()
        )


class GlobalUserProjectionRepository:
    def __init__(self, session):
        self.session = session

    async def get_by_user_id(self, user_id):
        return (
            await self.session.execute(
                select(GlobalUserProjection).where(GlobalUserProjection.user_id == user_id)
            )
        ).scalar_one_or_none()

    async def upsert(self, user_id):
        statement = insert(GlobalUserProjection).values(user_id=user_id)
        await self.session.execute(
            statement.on_conflict_do_update(
                index_elements=("user_id",), set_={"updated_at": func.now()}
            )
        )
        await self.session.flush()
        return await self.get_by_user_id(user_id)


class ProcessedEventRepository:
    def __init__(self, session):
        self.session = session

    async def exists(self, event_id):
        return (
            await self.session.execute(
                select(ProcessedEvent.id).where(ProcessedEvent.event_id == event_id)
            )
        ).scalar_one_or_none() is not None

    async def add(self, event_id, event_type, organization_id=None):
        row = ProcessedEvent(
            event_id=event_id, event_type=event_type, organization_id=organization_id
        )
        self.session.add(row)
        await self.session.flush()
        return row


class OutboxRepository:
    def __init__(self, session):
        self.session = session

    async def add(self, **values):
        row = OutboxEvent(**values)
        self.session.add(row)
        await self.session.flush()
        return row

    async def get_by_event_id(self, event_id):
        return (
            await self.session.execute(select(OutboxEvent).where(OutboxEvent.event_id == event_id))
        ).scalar_one_or_none()

    async def fetch_pending(self, organization_id, limit=100):
        return list(
            (
                await self.session.execute(
                    select(OutboxEvent)
                    .where(
                        OutboxEvent.organization_id == organization_id,
                        OutboxEvent.status == "PENDING",
                    )
                    .limit(limit)
                )
            ).scalars()
        )

    async def mark_published(self, organization_id, event_id):
        row = await self._get(organization_id, event_id)
        if row:
            row.status = "PUBLISHED"
        return row

    async def mark_retry(self, organization_id, event_id):
        row = await self._get(organization_id, event_id)
        if row:
            row.status = "PENDING"
        return row

    async def _get(self, organization_id, event_id):
        return (
            await self.session.execute(
                select(OutboxEvent).where(
                    OutboxEvent.organization_id == organization_id,
                    OutboxEvent.event_id == event_id,
                )
            )
        ).scalar_one_or_none()
