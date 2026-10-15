"""Company lifecycle notifications (invitations, group membership) — low-noise subset."""

from uuid import UUID

from app.db import SessionLocal
from app.fanout import NotificationFanout
from app.invitation_notifications import PendingInvitationRepository, deliver_invitation
from app.repositories import ProcessedEventRepository, ProjectionRepository

INVITATION_CREATED_EVENT = "invitation.created.v1"
LEGACY_MEMBER_INVITED_EVENTS = frozenset({"member.created.v2", "member.updated.v2"})
GROUP_MEMBER_EVENTS = frozenset({"conversation.member_added.v1"})


class UnsupportedOrgNotificationEvent(ValueError):
    pass


class OrgNotificationConsumer:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    async def consume(self, raw_event: dict) -> bool:
        event_type = raw_event.get("event_type")
        supported = (
            {INVITATION_CREATED_EVENT} | LEGACY_MEMBER_INVITED_EVENTS | GROUP_MEMBER_EVENTS
        )
        if event_type not in supported:
            raise UnsupportedOrgNotificationEvent("unsupported org notification event")
        organization_id = UUID(str(raw_event["organization_id"]))
        event_id = UUID(str(raw_event["event_id"]))
        payload = raw_event["payload"]
        async with self.session_factory() as session:
            async with session.begin():
                processed = ProcessedEventRepository(session)
                if await processed.exists(event_id):
                    return False
                fanout = NotificationFanout(session)
                pending_repo = PendingInvitationRepository(session)
                if event_type == INVITATION_CREATED_EVENT:
                    projections = ProjectionRepository(session)
                    invitation_id = UUID(str(payload.get("invitation_id", payload["resource_id"])))
                    recipient_user_id = payload.get("recipient_user_id")
                    user_id = UUID(str(recipient_user_id)) if recipient_user_id else None
                    await deliver_invitation(
                        fanout,
                        pending_repo,
                        projections,
                        organization_id=organization_id,
                        invitation_id=invitation_id,
                        recipient_user_id=user_id,
                        recipient_phone_e164=payload.get("recipient_phone_e164"),
                        recipient_email=payload.get("recipient_email"),
                    )
                elif event_type in LEGACY_MEMBER_INVITED_EVENTS:
                    if str(payload.get("status", "")).upper() != "INVITED":
                        await processed.add(event_id, event_type, organization_id)
                        return True
                    if payload.get("user_id") is None:
                        await processed.add(event_id, event_type, organization_id)
                        return True
                    member_id = UUID(str(payload["member_id"]))
                    user_id = UUID(str(payload["user_id"]))
                    invitation_id = UUID(str(payload.get("invitation_id", member_id)))
                    await fanout.notify_member(
                        organization_id=organization_id,
                        conversation_id=None,
                        message_id=invitation_id,
                        recipient_user_id=user_id,
                        recipient_member_id=member_id,
                        notification_type="INVITATION",
                        sender_user_id=None,
                        sender_label="Workspace",
                        is_group=False,
                        dedupe_message_id=invitation_id,
                    )
                elif event_type == "conversation.member_added.v1":
                    projections = ProjectionRepository(session)
                    conversation_id = UUID(str(payload["conversation_id"]))
                    conversation = await projections.get_conversation(
                        organization_id, conversation_id
                    )
                    if conversation is None or conversation.conversation_type != "GROUP":
                        await processed.add(event_id, event_type, organization_id)
                        return True
                    member_id = UUID(str(payload["member_id"]))
                    user_id = UUID(str(payload["user_id"]))
                    await fanout.notify_member(
                        organization_id=organization_id,
                        conversation_id=conversation_id,
                        message_id=UUID(str(payload.get("message_id", conversation_id))),
                        recipient_user_id=user_id,
                        recipient_member_id=member_id,
                        notification_type="GROUP",
                        sender_user_id=None,
                        sender_label=None,
                        is_group=True,
                        dedupe_message_id=conversation_id,
                    )
                await processed.add(event_id, event_type, organization_id)
        return True
