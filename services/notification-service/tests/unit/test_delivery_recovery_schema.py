from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.db import SessionLocal, engine
from app.repositories import NotificationDeliveryRepository, NotificationRepository


async def transaction():
    session = SessionLocal()
    await session.begin()
    return session


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_delivery_recovery_fields_persist_and_can_be_cleared():
    session, organization_id = await transaction(), uuid4()
    try:
        notification = await NotificationRepository(session).create(
            organization_id=organization_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            recipient_user_id=uuid4(),
            recipient_member_id=uuid4(),
            notification_type="MESSAGE",
            title=None,
            body=None,
            preview_mode="FULL",
        )
        claimed_at = datetime.now(UTC)
        delivery = await NotificationDeliveryRepository(session).create(
            organization_id=organization_id,
            notification_id=notification.id,
            device_push_token_id=uuid4(),
            device_id=uuid4(),
            provider="APNS",
            status="SENDING",
            attempt_count=1,
            claimed_at=claimed_at,
            last_error="temporary provider failure",
        )
        assert delivery.claimed_at == claimed_at
        assert delivery.last_error == "temporary provider failure"
        delivery.claimed_at = None
        delivery.last_error = None
        await session.flush()
        loaded = await NotificationDeliveryRepository(session).get_by_id(
            organization_id, delivery.id
        )
        assert loaded.claimed_at is None and loaded.last_error is None
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_delivery_recovery_fields_are_rollback_safe_without_repository_commit():
    session, organization_id = await transaction(), uuid4()
    delivery_id = None
    try:
        notification = await NotificationRepository(session).create(
            organization_id=organization_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            recipient_user_id=uuid4(),
            recipient_member_id=uuid4(),
            notification_type="MESSAGE",
            title=None,
            body=None,
            preview_mode="FULL",
        )
        delivery = await NotificationDeliveryRepository(session).create(
            organization_id=organization_id,
            notification_id=notification.id,
            device_push_token_id=uuid4(),
            device_id=uuid4(),
            provider="FCM",
            status="PENDING",
            claimed_at=datetime.now(UTC),
            last_error="sanitized failure",
        )
        delivery_id = delivery.id
    finally:
        await session.rollback()
        await session.close()

    verification = SessionLocal()
    try:
        assert (
            await NotificationDeliveryRepository(verification).get_by_id(
                organization_id, delivery_id
            )
            is None
        )
    finally:
        await verification.close()
