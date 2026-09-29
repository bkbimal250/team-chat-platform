from uuid import uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql

from app.db import SessionLocal, engine
from app.models import GlobalUserProjection
from app.repositories import (
    GlobalUserProjectionRepository,
    NotificationDeliveryRepository,
    NotificationRepository,
    OutboxRepository,
    ProcessedEventRepository,
    ProjectionRepository,
)


async def transaction():
    session = SessionLocal()
    await session.begin()
    return session


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


def notification_values(org, recipient):
    return {
        "organization_id": org,
        "conversation_id": uuid4(),
        "message_id": uuid4(),
        "recipient_user_id": uuid4(),
        "recipient_member_id": recipient,
        "notification_type": "MESSAGE",
        "title": "New message",
        "body": "hello",
        "preview_mode": "FULL",
    }


@pytest.mark.asyncio
async def test_notification_and_delivery_repositories_are_tenant_scoped_and_rollback_safe():
    session, org_a, org_b, recipient = await transaction(), uuid4(), uuid4(), uuid4()
    try:
        notifications = NotificationRepository(session)
        deliveries = NotificationDeliveryRepository(session)
        notification = await notifications.create(**notification_values(org_a, recipient))
        delivery = await deliveries.create(
            organization_id=org_a,
            notification_id=notification.id,
            device_push_token_id=uuid4(),
            device_id=uuid4(),
            provider="FCM",
            status="PENDING",
        )
        assert await notifications.get_by_id(org_a, notification.id) is notification
        assert await notifications.get_by_id(org_b, notification.id) is None
        assert await deliveries.get_by_id(org_a, delivery.id) is delivery
        assert await deliveries.get_by_id(org_b, delivery.id) is None
        assert (
            "SKIP LOCKED"
            in str(deliveries.claimable_query(org_a).compile(dialect=postgresql.dialect())).upper()
        )
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_notification_dedupe_and_create_many_use_real_session_flushes():
    session, org, recipient = await transaction(), uuid4(), uuid4()
    try:
        notifications = NotificationRepository(session)
        deliveries = NotificationDeliveryRepository(session)
        values = notification_values(org, recipient)
        notification = await notifications.create(**values)
        assert (
            await notifications.get_by_dedupe_identity(
                org, values["message_id"], recipient, "MESSAGE"
            )
            is notification
        )
        rows = await deliveries.create_many(
            [
                {
                    "organization_id": org,
                    "notification_id": notification.id,
                    "device_push_token_id": uuid4(),
                    "device_id": uuid4(),
                    "provider": "FCM",
                    "status": "PENDING",
                },
                {
                    "organization_id": org,
                    "notification_id": notification.id,
                    "device_push_token_id": uuid4(),
                    "device_id": uuid4(),
                    "provider": "APNS",
                    "status": "PENDING",
                },
            ]
        )
        assert len(rows) == 2
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_projection_upserts_and_active_member_lookup_are_tenant_scoped():
    session, org_a, org_b, member, conversation = (
        await transaction(),
        uuid4(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    try:
        projections = ProjectionRepository(session)
        await projections.upsert_user(
            organization_id=org_a, user_id=uuid4(), display_name="A", status="ACTIVE"
        )
        await projections.upsert_membership(
            organization_id=org_a, member_id=member, user_id=uuid4(), status="ACTIVE"
        )
        await projections.upsert_conversation(
            organization_id=org_a,
            conversation_id=conversation,
            conversation_type="DIRECT",
            status="ACTIVE",
        )
        await projections.upsert_conversation_member(
            organization_id=org_a,
            conversation_id=conversation,
            member_id=member,
            user_id=uuid4(),
            status="ACTIVE",
        )
        await projections.upsert_membership(
            organization_id=org_b, member_id=member, user_id=uuid4(), status="INACTIVE"
        )
        await projections.upsert_conversation(
            organization_id=org_b,
            conversation_id=conversation,
            conversation_type="CHANNEL",
            status="ACTIVE",
        )
        assert await projections.get_conversation(org_a, conversation)
        assert (
            await projections.get_conversation(org_b, conversation)
        ).conversation_type == "CHANNEL"
        assert (await projections.get_membership(org_a, member)).status == "ACTIVE"
        assert (await projections.get_membership(org_b, member)).status == "INACTIVE"
        assert len(await projections.active_conversation_members(org_a, conversation)) == 1
        assert not await projections.active_conversation_members(org_b, conversation)
        assert len(await projections.active_memberships(org_a)) == 1
        assert not await projections.active_memberships(org_b)
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_repository_operations_remain_rollback_safe_without_internal_commits():
    organization_id, event_id = uuid4(), uuid4()
    session = await transaction()
    try:
        outbox = OutboxRepository(session)
        await outbox.add(
            organization_id=organization_id,
            event_id=event_id,
            event_type="notification.sent.v1",
            payload={"notification_id": str(uuid4())},
        )
        assert len(await outbox.fetch_pending(organization_id)) == 1
    finally:
        await session.rollback()
        await session.close()

    verification_session = SessionLocal()
    try:
        assert await OutboxRepository(verification_session).fetch_pending(organization_id) == []
    finally:
        await verification_session.close()


@pytest.mark.asyncio
async def test_global_user_projection_upserts_and_looks_up_a_single_identity():
    session, user_id = await transaction(), uuid4()
    try:
        repository = GlobalUserProjectionRepository(session)
        assert await repository.get_by_user_id(user_id) is None
        created = await repository.upsert(user_id)
        updated = await repository.upsert(user_id)
        assert created.user_id == user_id
        assert updated.user_id == user_id
        assert await repository.get_by_user_id(user_id) is updated
        assert (
            await session.scalar(
                select(func.count())
                .select_from(GlobalUserProjection)
                .where(GlobalUserProjection.user_id == user_id)
            )
        ) == 1
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_global_user_projection_rollback_removes_uncommitted_change():
    user_id = uuid4()
    session = await transaction()
    try:
        await GlobalUserProjectionRepository(session).upsert(user_id)
        assert await GlobalUserProjectionRepository(session).get_by_user_id(user_id)
    finally:
        await session.rollback()
        await session.close()

    verification_session = SessionLocal()
    try:
        assert (
            await GlobalUserProjectionRepository(verification_session).get_by_user_id(user_id)
            is None
        )
    finally:
        await verification_session.close()


@pytest.mark.asyncio
async def test_processed_events_and_outbox_are_persistent_and_tenant_scoped():
    session, org_a, org_b, event_id = await transaction(), uuid4(), uuid4(), uuid4()
    try:
        processed = ProcessedEventRepository(session)
        outbox = OutboxRepository(session)
        assert not await processed.exists(event_id)
        await processed.add(event_id, "message.created.v1", org_a)
        assert await processed.exists(event_id)
        outbox_event = await outbox.add(
            organization_id=org_a,
            event_id=uuid4(),
            event_type="notification.sent.v1",
            payload={"notification_id": str(uuid4())},
        )
        assert await outbox.fetch_pending(org_a) == [outbox_event]
        assert await outbox.fetch_pending(org_b) == []
        await outbox.mark_published(org_a, outbox_event.event_id)
        assert outbox_event.status == "PUBLISHED"
        await outbox.mark_retry(org_a, outbox_event.event_id)
        assert outbox_event.status == "PENDING"
    finally:
        await session.rollback()
        await session.close()
