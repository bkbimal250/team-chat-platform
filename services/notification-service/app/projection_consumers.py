"""Notification-owned projections built from frozen upstream event contracts."""

import logging
from dataclasses import dataclass
from uuid import UUID

from app.db import SessionLocal
from app.repositories import (
    GlobalUserProjectionRepository,
    ProcessedEventRepository,
    ProjectionRepository,
)

logger = logging.getLogger(__name__)

GLOBAL_USER_EVENTS = frozenset(
    {
        "user.created.v1",
        "user.profile_updated.v1",
        "user.preferences_updated.v1",
        "user.privacy_updated.v1",
        "user.blocked.v1",
        "user.unblocked.v1",
    }
)
MEMBER_EVENTS = frozenset(
    {
        "member.created.v2",
        "member.updated.v2",
        "member.activated.v2",
        "member.suspended.v2",
        "member.left.v2",
        "member.removed.v2",
        "member.role_changed.v2",
    }
)
CONVERSATION_EVENTS = frozenset(
    {
        "conversation.created.v1",
        "conversation.updated.v1",
        "conversation.closed.v1",
        "conversation.member_added.v1",
        "conversation.member_removed.v1",
        "conversation.member_left.v1",
        "conversation.member_role_changed.v1",
        "conversation.ownership_transferred.v1",
        "conversation.state_updated.v1",
    }
)
MEMBER_CONVERSATION_EVENTS = frozenset(
    {
        "conversation.member_added.v1",
        "conversation.member_removed.v1",
        "conversation.member_left.v1",
        "conversation.member_role_changed.v1",
    }
)
INACTIVE_MEMBERSHIP_STATUSES = frozenset({"LEFT", "REMOVED"})


class UnsupportedProjectionEvent(ValueError):
    """The delivery is well-formed JSON but not a supported frozen contract."""


@dataclass(frozen=True)
class ProjectionEvent:
    event_id: UUID
    event_type: str
    event_version: int
    payload: dict
    organization_id: UUID | None
    correlation_id: str

    @classmethod
    def from_dict(cls, event: dict):
        try:
            event_id = UUID(str(event["event_id"]))
            event_type = event["event_type"]
            event_version = event["event_version"]
            payload = event["payload"]
        except (KeyError, TypeError, ValueError) as exc:
            raise UnsupportedProjectionEvent("malformed event envelope") from exc
        if not isinstance(payload, dict) or not isinstance(event_version, int):
            raise UnsupportedProjectionEvent("malformed event envelope")
        supported = (
            event_type in GLOBAL_USER_EVENTS
            or event_type in MEMBER_EVENTS
            or event_type in CONVERSATION_EVENTS
        )
        expected_version = 2 if event_type in MEMBER_EVENTS else 1
        if not supported or event_version != expected_version:
            raise UnsupportedProjectionEvent("unsupported event contract")
        organization_id = event.get("organization_id")
        if event_type in MEMBER_EVENTS | CONVERSATION_EVENTS:
            if organization_id is None:
                raise UnsupportedProjectionEvent("tenant event missing organization_id")
            organization_id = UUID(str(organization_id))
        return cls(
            event_id=event_id,
            event_type=event_type,
            event_version=event_version,
            payload=payload,
            organization_id=organization_id,
            correlation_id=str(event.get("correlation_id", "")),
        )


class ProjectionConsumer:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    async def consume(self, raw_event: dict) -> bool:
        event = ProjectionEvent.from_dict(raw_event)
        async with self.session_factory() as session:
            async with session.begin():
                processed = ProcessedEventRepository(session)
                if await processed.exists(event.event_id):
                    return False
                projections = ProjectionRepository(session)
                global_users = GlobalUserProjectionRepository(session)
                if event.event_type in GLOBAL_USER_EVENTS:
                    await self._apply_global_user(event, global_users, projections)
                elif event.event_type in MEMBER_EVENTS:
                    await self._apply_membership(event, global_users, projections)
                else:
                    await self._apply_conversation(event, projections)
                await processed.add(event.event_id, event.event_type, event.organization_id)
        logger.info(
            "projection_event_processed",
            extra={"event_id": str(event.event_id), "correlation_id": event.correlation_id},
        )
        return True

    async def _apply_global_user(self, event, global_users, projections):
        user_id = self._uuid(event.payload, "user_id")
        await global_users.upsert(user_id)
        for membership in await projections.memberships_for_user(user_id):
            if membership.status not in INACTIVE_MEMBERSHIP_STATUSES:
                await projections.upsert_user(
                    organization_id=membership.organization_id,
                    user_id=user_id,
                    display_name="",
                    status=membership.status,
                )

    async def _apply_membership(self, event, global_users, projections):
        organization_id = event.organization_id
        if (
            event.payload.get("participant_kind") == "UNLINKED_MEMBER"
            or event.payload.get("user_id") is None
        ):
            return
        member_id = self._uuid(event.payload, "member_id")
        user_id = self._uuid(event.payload, "user_id")
        status = self._required_text(event.payload, "status")
        await projections.upsert_membership(
            organization_id=organization_id, member_id=member_id, user_id=user_id, status=status
        )
        global_user = await global_users.get_by_user_id(user_id)
        current_user = await projections.get_user(organization_id, user_id)
        if current_user or (global_user and status not in INACTIVE_MEMBERSHIP_STATUSES):
            await projections.upsert_user(
                organization_id=organization_id,
                user_id=user_id,
                display_name="",
                status=status,
            )

    async def _apply_conversation(self, event, projections):
        organization_id = event.organization_id
        payload = event.payload
        conversation_id = self._uuid(payload, "conversation_id")
        if event.event_type not in MEMBER_CONVERSATION_EVENTS:
            await projections.upsert_conversation(
                organization_id=organization_id,
                conversation_id=conversation_id,
                conversation_type=self._required_text(payload, "type"),
                status=self._required_text(payload, "status"),
            )
        if event.event_type == "conversation.created.v1":
            for member in payload.get("members", []):
                await self._upsert_conversation_member(
                    organization_id, conversation_id, member, projections
                )
        elif event.event_type in MEMBER_CONVERSATION_EVENTS:
            await self._upsert_conversation_member(
                organization_id, conversation_id, payload, projections
            )

    async def _upsert_conversation_member(
        self, organization_id, conversation_id, payload, projections
    ):
        if payload.get("participant_kind") == "UNLINKED_MEMBER" or payload.get("user_id") is None:
            return
        status = payload.get("resulting_status", payload.get("status"))
        if not isinstance(status, str):
            raise UnsupportedProjectionEvent("conversation member missing status")
        await projections.upsert_conversation_member(
            organization_id=organization_id,
            conversation_id=conversation_id,
            member_id=self._uuid(payload, "member_id"),
            user_id=self._uuid(payload, "user_id"),
            status=status,
        )

    @staticmethod
    def _uuid(payload, key):
        try:
            return UUID(str(payload[key]))
        except (KeyError, TypeError, ValueError) as exc:
            raise UnsupportedProjectionEvent(f"payload missing {key}") from exc

    @staticmethod
    def _required_text(payload, key):
        value = payload.get(key)
        if not isinstance(value, str):
            raise UnsupportedProjectionEvent(f"payload missing {key}")
        return value
