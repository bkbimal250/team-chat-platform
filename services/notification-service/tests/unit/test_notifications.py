from uuid import uuid4

import pytest

from app.providers import FakePushProvider, ProviderResult
from app.schemas import TokenRequest
from app.security import Principal
from app.service import NotificationService


def setup():
    org, conversation, sender, recipient = uuid4(), uuid4(), uuid4(), uuid4()
    service = NotificationService(FakePushProvider())
    service.project_members(org, conversation, {sender, recipient})
    return service, org, conversation, sender, recipient


@pytest.mark.asyncio
async def test_token_rotation_preferences_and_removal():
    service, org, conversation, _, member = setup()
    principal = Principal(org, uuid4(), member, uuid4(), frozenset({conversation}))
    first = await service.put_token(
        principal, TokenRequest(platform="IOS", provider="APNS", push_token="a")
    )
    second = await service.put_token(
        principal, TokenRequest(platform="IOS", provider="APNS", push_token="b")
    )
    assert first.id == second.id and second.value == "b"
    assert (
        await service.patch_preferences(principal, {"notification_preview": "HIDDEN"})
    ).notification_preview == "HIDDEN"
    await service.remove_token(principal)
    assert not second.enabled


@pytest.mark.asyncio
async def test_message_consumer_excludes_sender_and_is_idempotent():
    service, org, conversation, sender, recipient = setup()
    await service.put_token(
        Principal(org, uuid4(), recipient, uuid4()),
        TokenRequest(platform="ANDROID", provider="FCM", push_token="x"),
    )
    event = {
        "event_id": "e1",
        "event_type": "message.created.v1",
        "organization_id": str(org),
        "payload": {
            "conversation_id": str(conversation),
            "sender_member_id": str(sender),
            "sender_name": "A",
            "body": "hello",
        },
    }
    assert await service.consume(event)
    assert len(service.deliveries) == 1
    assert not await service.consume(event)


@pytest.mark.asyncio
async def test_delivery_success_retry_and_invalid_token():
    service, org, conversation, sender, recipient = setup()
    token = await service.put_token(
        Principal(org, uuid4(), recipient, uuid4()),
        TokenRequest(platform="WEB", provider="WEB_PUSH", push_token="x"),
    )
    await service.consume(
        {
            "event_id": "e",
            "event_type": "message.created.v1",
            "organization_id": str(org),
            "payload": {"conversation_id": str(conversation), "sender_member_id": str(sender)},
        }
    )
    await service.send_pending()
    assert service.deliveries[0].status == "SENT"
    service.provider.result = ProviderResult(False, error_code="gone", token_invalid=True)
    service.deliveries[0].status = "PENDING"
    await service.send_pending()
    assert not token.enabled and service.deliveries[0].status == "CANCELLED"
