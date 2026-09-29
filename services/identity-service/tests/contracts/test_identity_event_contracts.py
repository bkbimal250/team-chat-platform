import uuid
from datetime import UTC, datetime

import pytest


@pytest.mark.parametrize(
    "event_type",
    [
        "member.activated.v1",
        "member.suspended.v1",
        "member.removed.v1",
        "member.role_changed.v1",
        "organization.suspended.v1",
        "identity.created.v1",
        "device.registered.v1",
        "device.revoked.v1",
        "session.created.v1",
        "session.revoked.v1",
        "security.refresh_reuse_detected.v1",
    ],
)
def test_identity_event_envelope(event_type):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": datetime.now(UTC).isoformat(),
        "producer": "identity-service",
        "organization_id": None,
        "aggregate_id": str(uuid.uuid4()),
        "correlation_id": "test",
        "payload": {},
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
