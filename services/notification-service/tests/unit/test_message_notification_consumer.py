import json
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.db import SessionLocal, engine
from app.message_notification_consumer import (
    MessageNotificationConsumer,
    MessageProjectionUnavailable,
)
from app.models import (
    ConversationMemberProjection,
    ConversationProjection,
    DevicePushToken,
    MembershipProjection,
    Notification,
    NotificationDelivery,
    NotificationPreference,
    OutboxEvent,
    ProcessedEvent,
)
from app.rabbit import consume_message_created_delivery
from app.repositories import OutboxRepository, PreferenceRepository, ProjectionRepository


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


def message_event(
    organization_id, conversation_id, sender_user_id, sender_member_id, message_id=None
):
    return {
        "event_id": str(uuid4()),
        "event_type": "message.created.v1",
        "event_version": 1,
        "organization_id": str(organization_id),
        "correlation_id": "message-notification-test",
        "payload": {
            "organization_id": str(organization_id),
            "conversation_id": str(conversation_id),
            "message_id": str(message_id or uuid4()),
            "sender_user_id": str(sender_user_id),
            "sender_member_id": str(sender_member_id),
            "sender_device_id": str(uuid4()),
            "type": "TEXT",
            "reply_to_message_id": None,
            "client_message_id": str(uuid4()),
            "sequence": 1,
            "created_at": "2026-01-01T00:00:00+00:00",
        },
    }


async def seed_recipient(
    organization_id,
    conversation_id,
    member_id,
    user_id,
    *,
    conversation_status="ACTIVE",
    member_status="ACTIVE",
    membership_status="ACTIVE",
    tokens=0,
    device_id=None,
    token_value=None,
):
    async with SessionLocal.begin() as session:
        projections = ProjectionRepository(session)
        await projections.upsert_conversation(
            organization_id=organization_id,
            conversation_id=conversation_id,
            conversation_type="GROUP",
            status=conversation_status,
        )
        await projections.upsert_conversation_member(
            organization_id=organization_id,
            conversation_id=conversation_id,
            member_id=member_id,
            user_id=user_id,
            status=member_status,
        )
        await projections.upsert_membership(
            organization_id=organization_id,
            member_id=member_id,
            user_id=user_id,
            status=membership_status,
        )
        for _ in range(tokens):
            session.add(
                DevicePushToken(
                    organization_id=organization_id,
                    user_id=user_id,
                    member_id=member_id,
                    device_id=device_id or uuid4(),
                    platform="IOS",
                    provider="APNS",
                    token=token_value or str(uuid4()),
                    enabled=True,
                )
            )


async def cleanup(organization_id):
    async with SessionLocal.begin() as session:
        for model in (
            NotificationDelivery,
            OutboxEvent,
            Notification,
            ProcessedEvent,
            NotificationPreference,
            DevicePushToken,
            ConversationMemberProjection,
            ConversationProjection,
            MembershipProjection,
        ):
            if hasattr(model, "organization_id"):
                await session.execute(delete(model).where(model.organization_id == organization_id))


@pytest.mark.asyncio
async def test_group_message_creates_logical_notifications_pending_deliveries_and_outbox():
    organization_id, conversation_id = uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_a, recipient_a_member = uuid4(), uuid4()
    recipient_b, recipient_b_member = uuid4(), uuid4()
    await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
    await seed_recipient(
        organization_id, conversation_id, recipient_a_member, recipient_a, tokens=1
    )
    await seed_recipient(
        organization_id, conversation_id, recipient_b_member, recipient_b, tokens=2
    )
    event = message_event(organization_id, conversation_id, sender_user, sender_member)
    try:
        assert await MessageNotificationConsumer().consume(event)
        async with SessionLocal() as session:
            notifications = (
                await session.scalars(
                    select(Notification).where(Notification.organization_id == organization_id)
                )
            ).all()
            deliveries = (
                await session.scalars(
                    select(NotificationDelivery).where(
                        NotificationDelivery.organization_id == organization_id
                    )
                )
            ).all()
            outbox = (
                await session.scalars(
                    select(OutboxEvent).where(OutboxEvent.organization_id == organization_id)
                )
            ).all()
            assert {row.recipient_member_id for row in notifications} == {
                recipient_a_member,
                recipient_b_member,
            }
            assert all(row.title is None and row.body is None for row in notifications)
            assert len(deliveries) == 3 and {row.status for row in deliveries} == {"PENDING"}
            assert len(outbox) == 2 and {row.event_type for row in outbox} == {
                "notification.created.v1"
            }
            assert await session.scalar(
                select(ProcessedEvent).where(ProcessedEvent.event_id == event["event_id"])
            )
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_inactive_memberships_and_conversation_members_are_excluded():
    organization_id, conversation_id = uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    inactive_member, inactive_user = uuid4(), uuid4()
    suspended_member, suspended_user = uuid4(), uuid4()
    await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
    await seed_recipient(
        organization_id,
        conversation_id,
        inactive_member,
        inactive_user,
        member_status="LEFT",
        tokens=1,
    )
    await seed_recipient(
        organization_id,
        conversation_id,
        suspended_member,
        suspended_user,
        membership_status="SUSPENDED",
        tokens=1,
    )
    try:
        assert await MessageNotificationConsumer().consume(
            message_event(organization_id, conversation_id, sender_user, sender_member)
        )
        async with SessionLocal() as session:
            assert not (
                await session.scalars(
                    select(Notification).where(Notification.organization_id == organization_id)
                )
            ).all()
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_push_disabled_and_no_token_keep_logical_notification_without_delivery():
    organization_id, conversation_id = uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_user, recipient_member = uuid4(), uuid4()
    await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
    await seed_recipient(organization_id, conversation_id, recipient_member, recipient_user)

    async with SessionLocal.begin() as session:
        await PreferenceRepository(session).upsert(
            organization_id, recipient_member, push_enabled=False, preview="HIDDEN"
        )
    try:
        assert await MessageNotificationConsumer().consume(
            message_event(organization_id, conversation_id, sender_user, sender_member)
        )
        async with SessionLocal() as session:
            assert (
                len(
                    (
                        await session.scalars(
                            select(Notification).where(
                                Notification.organization_id == organization_id
                            )
                        )
                    ).all()
                )
                == 1
            )
            assert not (
                await session.scalars(
                    select(NotificationDelivery).where(
                        NotificationDelivery.organization_id == organization_id
                    )
                )
            ).all()
            notification = await session.scalar(
                select(Notification).where(Notification.organization_id == organization_id)
            )
            outbox = await session.scalar(
                select(OutboxEvent).where(OutboxEvent.organization_id == organization_id)
            )
            assert notification.preview_mode == outbox.payload["preview_mode"] == "HIDDEN"
            assert "body" not in outbox.payload
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_preferences_and_tokens_are_isolated_by_organization():
    organization_a, organization_b, conversation_id = uuid4(), uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_user, recipient_member, shared_device_id = uuid4(), uuid4(), uuid4()
    for organization_id in (organization_a, organization_b):
        await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
        await seed_recipient(
            organization_id,
            conversation_id,
            recipient_member,
            recipient_user,
            tokens=1,
            device_id=shared_device_id,
            token_value="same-token-value",
        )
    async with SessionLocal.begin() as session:
        preferences = PreferenceRepository(session)
        await preferences.upsert(
            organization_a, recipient_member, push_enabled=False, preview="HIDDEN"
        )
        await preferences.upsert(
            organization_b, recipient_member, push_enabled=True, preview="FULL"
        )
    try:
        consumer = MessageNotificationConsumer()
        assert await consumer.consume(
            message_event(organization_a, conversation_id, sender_user, sender_member)
        )
        assert await consumer.consume(
            message_event(organization_b, conversation_id, sender_user, sender_member)
        )
        async with SessionLocal() as session:
            deliveries_a = (
                await session.scalars(
                    select(NotificationDelivery).where(
                        NotificationDelivery.organization_id == organization_a
                    )
                )
            ).all()
            deliveries_b = (
                await session.scalars(
                    select(NotificationDelivery).where(
                        NotificationDelivery.organization_id == organization_b
                    )
                )
            ).all()
            notification_a = await session.scalar(
                select(Notification).where(Notification.organization_id == organization_a)
            )
            notification_b = await session.scalar(
                select(Notification).where(Notification.organization_id == organization_b)
            )
            outbox_a = await session.scalar(
                select(OutboxEvent).where(OutboxEvent.organization_id == organization_a)
            )
            outbox_b = await session.scalar(
                select(OutboxEvent).where(OutboxEvent.organization_id == organization_b)
            )
            assert not deliveries_a and len(deliveries_b) == 1
            assert notification_a.preview_mode == outbox_a.payload["preview_mode"] == "HIDDEN"
            assert notification_b.preview_mode == outbox_b.payload["preview_mode"] == "FULL"
            assert "body" not in outbox_a.payload and "body" not in outbox_b.payload
    finally:
        await cleanup(organization_a)
        await cleanup(organization_b)


@pytest.mark.asyncio
async def test_duplicate_event_and_delivery_identity_are_safe():
    organization_id, conversation_id = uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_user, recipient_member = uuid4(), uuid4()
    await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
    await seed_recipient(
        organization_id, conversation_id, recipient_member, recipient_user, tokens=1
    )
    event = message_event(organization_id, conversation_id, sender_user, sender_member)
    try:
        consumer = MessageNotificationConsumer()
        assert await consumer.consume(event)
        assert not await consumer.consume(event)
        async with SessionLocal() as session:
            assert await session.scalar(
                select(Notification).where(Notification.organization_id == organization_id)
            )
            assert (
                len(
                    (
                        await session.scalars(
                            select(NotificationDelivery).where(
                                NotificationDelivery.organization_id == organization_id
                            )
                        )
                    ).all()
                )
                == 1
            )
            assert (
                len(
                    (
                        await session.scalars(
                            select(OutboxEvent).where(
                                OutboxEvent.organization_id == organization_id
                            )
                        )
                    ).all()
                )
                == 1
            )
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_cross_tenant_conversation_and_same_ids_stay_isolated():
    organization_a, organization_b, conversation_id = uuid4(), uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_user, recipient_member = uuid4(), uuid4()
    await seed_recipient(organization_b, conversation_id, sender_member, sender_user)
    await seed_recipient(
        organization_b, conversation_id, recipient_member, recipient_user, tokens=1
    )
    try:
        with pytest.raises(MessageProjectionUnavailable):
            await MessageNotificationConsumer().consume(
                message_event(organization_a, conversation_id, sender_user, sender_member)
            )
        async with SessionLocal() as session:
            assert not (
                await session.scalars(
                    select(Notification).where(Notification.organization_id == organization_b)
                )
            ).all()
            assert not await session.scalar(
                select(ProcessedEvent).where(ProcessedEvent.organization_id == organization_a)
            )
    finally:
        await cleanup(organization_a)
        await cleanup(organization_b)


@pytest.mark.asyncio
async def test_failure_rolls_back_and_rabbit_acks_only_after_commit(monkeypatch):
    organization_id, conversation_id = uuid4(), uuid4()
    sender_user, sender_member = uuid4(), uuid4()
    recipient_user, recipient_member = uuid4(), uuid4()
    await seed_recipient(organization_id, conversation_id, sender_member, sender_user)
    await seed_recipient(organization_id, conversation_id, recipient_member, recipient_user)
    event = message_event(organization_id, conversation_id, sender_user, sender_member)

    class Channel:
        def __init__(self):
            self.calls = []

        def basic_ack(self, tag):
            self.calls.append(("ack", tag))

        def basic_nack(self, tag, requeue):
            self.calls.append(("nack", tag, requeue))

    channel = Channel()
    try:
        await consume_message_created_delivery(
            MessageNotificationConsumer(), channel, 1, json.dumps(event).encode()
        )
        assert channel.calls == [("ack", 1)]

        async def fail_outbox(self, **_):
            raise RuntimeError("database write failed")

        monkeypatch.setattr(OutboxRepository, "add", fail_outbox)
        failed_event = message_event(organization_id, conversation_id, sender_user, sender_member)
        await consume_message_created_delivery(
            MessageNotificationConsumer(), channel, 2, json.dumps(failed_event).encode()
        )
        assert channel.calls == [("ack", 1), ("nack", 2, True)]
        async with SessionLocal() as session:
            assert not await session.scalar(
                select(ProcessedEvent).where(ProcessedEvent.event_id == failed_event["event_id"])
            )
    finally:
        await cleanup(organization_id)
