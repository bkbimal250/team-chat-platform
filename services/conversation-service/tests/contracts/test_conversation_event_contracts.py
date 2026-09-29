from types import SimpleNamespace

import pytest

from app.models import CStatus, CType, MRole, MStatus
from app.services import event


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


@pytest.mark.asyncio
async def test_human_conversation_member_event_contains_authoritative_identity():
    class Result:
        def scalars(self):
            return self

        def all(self):
            return [member]

    class Session:
        def __init__(self):
            self.added = []

        async def execute(self, _):
            return Result()

        def add(self, value):
            self.added.append(value)

    conversation = SimpleNamespace(
        id="conversation-id",
        organization_id="organization-id",
        type=CType.GROUP,
        status=CStatus.ACTIVE,
        created_at=None,
        updated_at=None,
    )
    member = SimpleNamespace(
        member_id="member-id", user_id="user-id", role=MRole.MEMBER, status=MStatus.ACTIVE
    )
    session = Session()

    await event(session, "conversation.member_added.v1", conversation, "correlation", member=member)

    payload = session.added[0].payload
    assert payload["organization_id"] == "organization-id"
    assert payload["conversation_id"] == "conversation-id"
    assert payload["member_id"] == "member-id"
    assert payload["user_id"] == "user-id"
    assert payload["participant_kind"] == "HUMAN"
    assert payload["resulting_status"] == MStatus.ACTIVE
