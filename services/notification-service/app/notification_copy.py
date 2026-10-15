"""Safe notification copy — never embed raw message or media content."""


def push_copy(notification_type: str, preview_mode: str, sender_label: str | None = None) -> tuple[str, str]:
    sender = (sender_label or "Someone").strip() or "Someone"
    if preview_mode == "HIDDEN":
        titles = {
            "MESSAGE": "New message",
            "MENTION": "New mention",
            "REACTION": "New reaction",
            "GROUP": "Group update",
            "INVITATION": "Workspace invitation",
        }
        return titles.get(notification_type, "Notification"), "Open the app to view"
    if preview_mode == "SENDER_ONLY":
        bodies = {
            "MESSAGE": "Sent you a message",
            "MENTION": "Mentioned you",
            "REACTION": "Reacted to your message",
            "GROUP": "Group conversation update",
            "INVITATION": "You have a pending invitation",
        }
        return sender, bodies.get(notification_type, "New activity")
    bodies = {
        "MESSAGE": "Sent you a message",
        "MENTION": "Mentioned you",
        "REACTION": "Reacted to your message",
        "GROUP": "You were added to a group",
        "INVITATION": "You have a pending workspace invitation",
    }
    return sender, bodies.get(notification_type, "New activity")
