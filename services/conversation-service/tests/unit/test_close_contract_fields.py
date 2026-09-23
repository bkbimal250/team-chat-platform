from app.models import Conversation, CStatus, MemberState


def test_conversation_supports_closed_lifecycle_timestamp():
    conversation = Conversation(status=CStatus.CLOSED)
    assert conversation.status == CStatus.CLOSED
    assert hasattr(conversation, "closed_at")


def test_member_state_exposes_resulting_contract_fields():
    state = MemberState(is_archived=True, is_pinned=True, notification_level="MENTIONS")
    assert state.is_archived is True
    assert state.is_pinned is True
    assert state.notification_level == "MENTIONS"
