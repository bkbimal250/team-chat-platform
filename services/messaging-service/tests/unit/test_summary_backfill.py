from datetime import UTC, datetime
from uuid import uuid4

from app.conversation_summary_rebuild import message_snapshot, read_snapshot
from app.models import ConversationReadState, Message


def test_summary_backfill_does_not_replay_notification_or_realtime_message_routes():
    created = datetime(2026, 1, 1, tzinfo=UTC)
    edited = datetime(2026, 1, 2, tzinfo=UTC)
    message = Message(
        id=uuid4(),
        organization_id=uuid4(),
        conversation_id=uuid4(),
        sender_user_id=uuid4(),
        sender_member_id=uuid4(),
        sender_device_id=uuid4(),
        client_message_id=uuid4(),
        sequence=1,
        type="TEXT",
        text="Updated",
        created_at=created,
        edited_at=edited,
    )
    snapshot = message_snapshot(message)
    assert snapshot.event_type == "conversation.summary.message.v1"
    assert snapshot.payload["source_kind"] == "message.edited.v1"
    assert snapshot.payload["version_at"] == edited.isoformat()
    row = ConversationReadState(
        organization_id=message.organization_id,
        conversation_id=message.conversation_id,
        member_id=uuid4(),
        last_read_sequence=7,
    )
    assert read_snapshot(row).payload["sequence"] == 7
    assert read_snapshot(row).event_type == "conversation.summary.read.v1"
