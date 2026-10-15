"""Cross-service contract smoke tests (no external infra)."""

import sys
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

import pytest

ROOT = Path(__file__).resolve().parents[2]
MESSAGING_ROOT = ROOT / "services" / "messaging-service"
NOTIFICATION_ROOT = ROOT / "services" / "notification-service"


def test_message_created_null_org_and_mentions():
    sys.path.insert(0, str(MESSAGING_ROOT))
    from app.services import event

    message = SimpleNamespace(
        id=uuid4(),
        organization_id=None,
        conversation_id=uuid4(),
        sender_user_id=uuid4(),
        sender_member_id=uuid4(),
        sender_device_id=uuid4(),
        type="TEXT",
        text="hi @team",
        reply_to_message_id=None,
        forward_from_message_id=None,
        forward_from_conversation_id=None,
        client_message_id=uuid4(),
        sequence=1,
        created_at=datetime.now(UTC),
    )
    mentioned = uuid4()
    outbox = event(
        message, "message.created.v1", "corr", mentioned_member_ids=[str(mentioned)]
    )
    assert outbox.payload["organization_id"] is None
    assert outbox.payload["mentioned_member_ids"] == [str(mentioned)]


def test_message_reaction_reactor_fields():
    sys.path.insert(0, str(MESSAGING_ROOT))
    from app.services import event

    message = SimpleNamespace(
        id=uuid4(),
        organization_id=uuid4(),
        conversation_id=uuid4(),
        sender_user_id=uuid4(),
        sender_member_id=uuid4(),
        sender_device_id=uuid4(),
        type="TEXT",
        text="hi",
        reply_to_message_id=None,
        forward_from_message_id=None,
        forward_from_conversation_id=None,
        client_message_id=uuid4(),
        sequence=1,
        created_at=datetime.now(UTC),
    )
    reactor_member = uuid4()
    outbox = event(
        message,
        "message.reaction_added.v1",
        "corr",
        reactor_member_id=str(reactor_member),
        reactor_user_id=str(uuid4()),
        reaction="👍",
    )
    assert outbox.payload["reactor_member_id"] == str(reactor_member)


@pytest.mark.integration
def test_live_stack_optional():
    import os

    if not os.getenv("GLOBALCHAT_INTEGRATION_URL"):
        pytest.skip("Set GLOBALCHAT_INTEGRATION_URL for live stack E2E (e.g. http://127.0.0.1:8008)")
