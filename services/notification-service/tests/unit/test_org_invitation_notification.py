import pytest
from uuid import uuid4

from app.org_notification_consumer import OrgNotificationConsumer


@pytest.mark.asyncio
async def test_invitation_created_stores_pending_without_user():
    consumer = OrgNotificationConsumer()
    event = {
        "event_id": str(uuid4()),
        "event_type": "invitation.created.v1",
        "event_version": 1,
        "organization_id": str(uuid4()),
        "correlation_id": "invite",
        "payload": {
            "resource_id": str(uuid4()),
            "invitation_id": str(uuid4()),
            "changed_fields": [],
            "status": "PENDING",
            "recipient_phone_e164": "+919999999999",
        },
    }
    event["payload"]["invitation_id"] = event["payload"]["resource_id"]
    # Requires database — skip when notification DB is not configured for unit sqlite
    try:
        result = await consumer.consume(event)
    except Exception as exc:
        if "connection" in str(exc).lower() or "database" in str(exc).lower():
            pytest.skip("notification database unavailable")
        raise
    assert result is True
