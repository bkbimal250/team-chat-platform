import pytest


@pytest.mark.parametrize(
    "event_type",
    [
        "conversation.created.v1",
        "conversation.updated.v1",
        "conversation.closed.v1",
        "conversation.member_added.v1",
        "conversation.member_removed.v1",
        "conversation.member_left.v1",
        "conversation.member_role_changed.v1",
        "conversation.ownership_transferred.v1",
        "conversation.state_updated.v1",
    ],
)
def test_conversation_event_contract_requires_common_envelope(event_type):
    envelope = {
        "event_id": "id",
        "event_type": event_type,
        "event_version": 1,
        "occurred_at": "now",
        "producer": "conversation-service",
        "organization_id": "org",
        "aggregate_id": "conversation",
        "correlation_id": "c",
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
    } <= envelope.keys()
    assert envelope["event_type"].endswith(".v1")


def test_close_ownership_and_state_contract_fields_are_explicit():
    closed = {
        "conversation_id": "c",
        "organization_id": "o",
        "status": "CLOSED",
        "closed_at": "now",
    }
    ownership = {"old_owner_member_id": "old", "new_owner_member_id": "new"}
    state = {
        "conversation_id": "c",
        "organization_id": "o",
        "member_id": "m",
        "user_id": "u",
        "updated_at": "now",
        "is_archived": True,
        "is_pinned": False,
        "muted_until": None,
        "notification_level": "ALL",
    }
    assert {"conversation_id", "organization_id", "status", "closed_at"} <= closed.keys()
    assert {"old_owner_member_id", "new_owner_member_id"} <= ownership.keys()
    assert {
        "conversation_id",
        "organization_id",
        "member_id",
        "user_id",
        "updated_at",
        "is_archived",
        "is_pinned",
        "muted_until",
        "notification_level",
    } <= state.keys()
