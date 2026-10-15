"""Transactional projection-backed consumer for Messaging notification events."""

from uuid import UUID

from app.db import SessionLocal
from app.fanout import NotificationFanout
from app.repositories import ProcessedEventRepository, ProjectionRepository

MESSAGE_CREATED_EVENT = "message.created.v1"
REACTION_ADDED_EVENT = "message.reaction_added.v1"
SUPPORTED_EVENTS = frozenset({MESSAGE_CREATED_EVENT, REACTION_ADDED_EVENT})


class UnsupportedMessageEvent(ValueError):
    """A malformed or unsupported message contract that should be discarded."""


class MessageProjectionUnavailable(RuntimeError):
    """A required local projection has not arrived yet; delivery should be retried."""


def _parse_org(raw_event: dict, payload: dict) -> UUID | None:
    raw = raw_event.get("organization_id", payload.get("organization_id"))
    if raw in {None, ""}:
        return None
    return UUID(str(raw))


class MessageNotificationConsumer:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    async def consume(self, raw_event: dict) -> bool:
        event_type = raw_event.get("event_type")
        if event_type not in SUPPORTED_EVENTS:
            raise UnsupportedMessageEvent("unsupported message event contract")
        if raw_event.get("event_version") != 1:
            raise UnsupportedMessageEvent("unsupported message event contract")
        payload = raw_event.get("payload")
        if not isinstance(payload, dict):
            raise UnsupportedMessageEvent("message event payload must be an object")
        organization_id = _parse_org(raw_event, payload)
        event_id = UUID(str(raw_event["event_id"]))
        conversation_id = UUID(str(payload["conversation_id"]))
        message_id = UUID(str(payload["message_id"]))
        sender_user_id = UUID(str(payload["sender_user_id"]))
        sender_member_id = UUID(str(payload["sender_member_id"]))
        async with self.session_factory() as session:
            async with session.begin():
                processed_events = ProcessedEventRepository(session)
                if await processed_events.exists(event_id):
                    return False
                projections = ProjectionRepository(session)
                conversation = await projections.get_conversation(organization_id, conversation_id)
                if conversation is None or conversation.status != "ACTIVE":
                    raise MessageProjectionUnavailable(
                        "active tenant conversation projection is unavailable"
                    )
                is_group = conversation.conversation_type == "GROUP"
                fanout = NotificationFanout(session)
                if event_type == MESSAGE_CREATED_EVENT:
                    await self._fanout_message(
                        fanout,
                        projections,
                        organization_id,
                        conversation_id,
                        message_id,
                        sender_user_id,
                        sender_member_id,
                        is_group,
                        payload,
                    )
                else:
                    reactor_member = payload.get("reactor_member_id") or payload.get(
                        "actor_member_id"
                    )
                    if reactor_member and UUID(str(reactor_member)) == sender_member_id:
                        pass
                    else:
                        await fanout.notify_member(
                            organization_id=organization_id,
                            conversation_id=conversation_id,
                            message_id=message_id,
                            recipient_user_id=sender_user_id,
                            recipient_member_id=sender_member_id,
                            notification_type="REACTION",
                            sender_user_id=UUID(str(reactor_member))
                            if reactor_member
                            else None,
                            sender_label=None,
                            is_group=is_group,
                            dedupe_message_id=message_id,
                        )
                await processed_events.add(event_id, event_type, organization_id)
        return True

    async def _fanout_message(
        self,
        fanout: NotificationFanout,
        projections: ProjectionRepository,
        organization_id,
        conversation_id,
        message_id,
        sender_user_id,
        sender_member_id,
        is_group,
        payload,
    ):
        mentioned = {
            UUID(str(value))
            for value in payload.get("mentioned_member_ids", [])
            if value is not None
        }
        members = await projections.active_conversation_members(organization_id, conversation_id)
        for conversation_member in members:
            if (
                conversation_member.member_id == sender_member_id
                or conversation_member.user_id == sender_user_id
            ):
                continue
            membership = await projections.get_membership(
                organization_id, conversation_member.member_id
            )
            if (
                organization_id is not None
                and (
                    membership is None
                    or membership.status != "ACTIVE"
                    or membership.user_id != conversation_member.user_id
                )
            ):
                continue
            notification_type = (
                "MENTION" if conversation_member.member_id in mentioned else "MESSAGE"
            )
            await fanout.notify_member(
                organization_id=organization_id,
                conversation_id=conversation_id,
                message_id=message_id,
                recipient_user_id=conversation_member.user_id,
                recipient_member_id=conversation_member.member_id,
                notification_type=notification_type,
                sender_user_id=sender_user_id,
                sender_label=payload.get("sender_name"),
                is_group=is_group,
                dedupe_message_id=message_id,
            )
