from uuid import uuid4

import pytest

from app.db import SessionLocal, engine
from app.delivery_worker import DeliveryWorker
from app.models import DevicePushToken
from app.repositories import (
    NotificationDeliveryRepository,
    NotificationRepository,
    PreferenceRepository,
    ProjectionRepository,
    PushTokenRepository,
)
from app.schemas import PreferencePatch, TokenRequest


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_tenant_scoped_repository_surfaces_reject_wrong_organization_ids():
    session = SessionLocal()
    await session.begin()
    organization_a, organization_b = uuid4(), uuid4()
    user_id, member_id, conversation_id = uuid4(), uuid4(), uuid4()
    try:
        notification = await NotificationRepository(session).create(
            organization_id=organization_a,
            conversation_id=conversation_id,
            message_id=uuid4(),
            recipient_user_id=user_id,
            recipient_member_id=member_id,
            notification_type="MESSAGE",
            title=None,
            body=None,
            preview_mode="FULL",
        )
        token = DevicePushToken(
            organization_id=organization_a,
            user_id=user_id,
            member_id=member_id,
            device_id=uuid4(),
            platform="IOS",
            provider="APNS",
            token="security-test-token",
            enabled=True,
        )
        session.add(token)
        await session.flush()
        delivery = await NotificationDeliveryRepository(session).create(
            organization_id=organization_a,
            notification_id=notification.id,
            device_push_token_id=token.id,
            device_id=token.device_id,
            provider="APNS",
            status="PENDING",
        )
        preferences = PreferenceRepository(session)
        await preferences.upsert(organization_a, member_id, push_enabled=False, preview="HIDDEN")
        projections = ProjectionRepository(session)
        await projections.upsert_user(
            organization_id=organization_a, user_id=user_id, display_name="", status="ACTIVE"
        )
        await projections.upsert_membership(
            organization_id=organization_a, member_id=member_id, user_id=user_id, status="ACTIVE"
        )
        await projections.upsert_conversation(
            organization_id=organization_a,
            conversation_id=conversation_id,
            conversation_type="GROUP",
            status="ACTIVE",
        )
        await projections.upsert_conversation_member(
            organization_id=organization_a,
            conversation_id=conversation_id,
            member_id=member_id,
            user_id=user_id,
            status="ACTIVE",
        )

        assert (
            await NotificationRepository(session).get_by_id(organization_b, notification.id) is None
        )
        assert (
            await NotificationDeliveryRepository(session).get_by_id(organization_b, delivery.id)
            is None
        )
        assert await PushTokenRepository(session).get_by_id(organization_b, token.id) is None
        assert await preferences.get(organization_b, member_id) is None
        assert await projections.get_user(organization_b, user_id) is None
        assert await projections.get_membership(organization_b, member_id) is None
        assert await projections.get_conversation(organization_b, conversation_id) is None
        assert (
            await projections.get_conversation_member(organization_b, conversation_id, member_id)
            is None
        )
    finally:
        await session.rollback()
        await session.close()


def test_public_token_and_preference_inputs_cannot_supply_identity_fields():
    with pytest.raises(Exception):
        TokenRequest(
            platform="IOS",
            provider="APNS",
            push_token="client-token",
            organization_id=str(uuid4()),
            user_id=str(uuid4()),
            member_id=str(uuid4()),
        )
    with pytest.raises(Exception):
        PreferencePatch(push_enabled=False, organization_id=str(uuid4()), member_id=str(uuid4()))


def test_provider_errors_never_persist_credentials_or_authorization_values():
    assert DeliveryWorker._sanitize_error("temporary@failure") == "temporary_failure"
    for unsafe in (
        "Authorization: Bearer credential-value",
        "token=provider-secret",
        "password: database-value",
        "private key material",
    ):
        assert DeliveryWorker._sanitize_error(unsafe) == "provider delivery failed"
