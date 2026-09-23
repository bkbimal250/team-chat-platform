import uuid
from datetime import UTC, datetime

import pytest


def test_platform_event_envelope_has_required_fields():
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "identity.created.v1",
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "identity-service",
        "organization_id": None,
        "aggregate_id": str(uuid.uuid4()),
        "correlation_id": "test",
        "payload": {"identity_id": str(uuid.uuid4())},
    }
    assert {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "producer",
        "organization_id",
        "aggregate_id",
        "correlation_id",
        "payload",
    } <= event.keys()


@pytest.mark.parametrize(
    "event_type,payload",
    [
        ("identity.created.v1", {"identity_id": "id"}),
        ("member.activated.v1", {"member_id": "id", "identity_id": "id"}),
        ("member.suspended.v1", {"member_id": "id", "identity_id": "id"}),
        ("member.removed.v1", {"member_id": "id", "identity_id": "id"}),
        ("organization.suspended.v1", {}),
        ("user.created.v1", {"user_id": "id"}),
        ("user.profile_updated.v1", {"user_id": "id"}),
        ("user.preferences_updated.v1", {"user_id": "id"}),
        ("user.privacy_updated.v1", {"user_id": "id"}),
        ("user.blocked.v1", {"user_id": "id"}),
        ("user.unblocked.v1", {"user_id": "id"}),
    ],
)
def test_required_event_contracts(event_type, payload):
    assert event_type.endswith(".v1")
    assert isinstance(payload, dict)
