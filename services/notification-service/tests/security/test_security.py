from uuid import uuid4

import pytest

from app.providers import FakePushProvider
from app.schemas import TokenRequest
from app.security import Principal
from app.service import NotificationService


@pytest.mark.asyncio
async def test_removed_member_and_revoked_device_never_receive_push():
    org, conversation, sender, recipient = uuid4(), uuid4(), uuid4(), uuid4()
    service = NotificationService(FakePushProvider())
    service.project_members(org, conversation, {sender, recipient})
    principal = Principal(org, uuid4(), recipient, uuid4())
    token = await service.put_token(
        principal, TokenRequest(platform="IOS", provider="APNS", push_token="x")
    )
    await service.consume(
        {
            "event_id": "r",
            "event_type": "conversation.member_removed.v1",
            "organization_id": str(org),
            "payload": {"conversation_id": str(conversation), "member_id": str(recipient)},
        }
    )
    await service.consume(
        {
            "event_id": "m",
            "event_type": "message.created.v1",
            "organization_id": str(org),
            "payload": {"conversation_id": str(conversation), "sender_member_id": str(sender)},
        }
    )
    assert not service.deliveries
    await service.consume(
        {
            "event_id": "d",
            "event_type": "device.revoked.v1",
            "organization_id": str(org),
            "payload": {"device_id": str(token.device_id)},
        }
    )
    assert not token.enabled


def test_client_token_body_cannot_impersonate_identity():
    with pytest.raises(Exception):
        TokenRequest(
            platform="IOS",
            provider="APNS",
            push_token="x",
            organization_id=uuid4(),
            device_id=uuid4(),
        )
