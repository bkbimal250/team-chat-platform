from app.notification_copy import push_copy


def test_hidden_preview_never_includes_message_body():
    title, body = push_copy("MESSAGE", "HIDDEN", "Alice")
    assert "Alice" not in body
    assert title == "New message"


def test_sender_only_uses_sender_without_message_text():
    title, body = push_copy("MENTION", "SENDER_ONLY", "Alice")
    assert title == "Alice"
    assert "@" not in body and "secret" not in body
