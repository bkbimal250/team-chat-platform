import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.providers import ProviderResult


def now():
    return datetime.now(UTC)


@dataclass
class Token:
    id: UUID
    organization_id: UUID
    user_id: UUID
    member_id: UUID
    device_id: UUID
    platform: str
    provider: str
    value: str
    enabled: bool = True
    invalidated_at: datetime | None = None


@dataclass
class Preference:
    push_enabled: bool = True
    message_notifications: bool = True
    group_notifications: bool = True
    notification_preview: str = "FULL"
    sound_enabled: bool = True
    vibration_enabled: bool = True


@dataclass
class Delivery:
    id: UUID
    notification_id: UUID
    token_id: UUID
    status: str = "PENDING"
    attempt_count: int = 0
    error_code: str | None = None
    next_attempt_at: datetime | None = None


class NotificationService:
    def __init__(self, provider, max_attempts=3, max_concurrent_sends=5):
        self.provider, self.max_attempts, self.max_concurrent_sends = (
            provider,
            max_attempts,
            max_concurrent_sends,
        )
        self.tokens, self.preferences, self.memberships = {}, {}, {}
        self.closed_conversations, self.processed_events, self.notifications = set(), set(), []
        self.deliveries, self.outbox = [], []

    def _key(self, principal):
        return (principal.organization_id, principal.member_id)

    def preference(self, principal):
        return self.preferences.setdefault(self._key(principal), Preference())

    async def put_token(self, principal, request):
        for token in self.tokens.values():
            if (
                token.organization_id == principal.organization_id
                and token.device_id == principal.device_id
            ):
                token.platform, token.provider, token.value, token.enabled = (
                    request.platform,
                    request.provider,
                    request.push_token,
                    True,
                )
                token.invalidated_at = None
                return token
        token = Token(
            uuid4(),
            principal.organization_id,
            principal.user_id,
            principal.member_id,
            principal.device_id,
            request.platform,
            request.provider,
            request.push_token,
        )
        self.tokens[token.id] = token
        return token

    async def remove_token(self, principal):
        for token in self.tokens.values():
            if (
                token.organization_id == principal.organization_id
                and token.device_id == principal.device_id
            ):
                token.enabled, token.invalidated_at = False, now()

    async def patch_preferences(self, principal, values):
        pref = self.preference(principal)
        for name, value in values.items():
            if value is not None:
                if name == "notification_preview" and value not in {
                    "FULL",
                    "SENDER_ONLY",
                    "HIDDEN",
                }:
                    raise HTTPException(422, "invalid preview setting")
                setattr(pref, name, value)
        return pref

    def project_members(self, organization_id, conversation_id, member_ids, kind="GROUP"):
        self.memberships[(organization_id, conversation_id)] = {
            "members": set(member_ids),
            "kind": kind,
        }

    def _payload(self, pref, sender, body):
        if pref.notification_preview == "HIDDEN":
            return {"title": "New message", "body": "New message"}
        if pref.notification_preview == "SENDER_ONLY":
            return {"title": sender, "body": "New message"}
        return {"title": sender, "body": body[:200]}

    async def consume(self, event):
        event_id, event_type = event["event_id"], event["event_type"]
        if event_id in self.processed_events:
            return False
        org, payload = UUID(event["organization_id"]), event["payload"]
        if event_type in {"conversation.member_removed.v1", "conversation.member_left.v1"}:
            self.memberships.get((org, UUID(payload["conversation_id"])), {"members": set()})[
                "members"
            ].discard(UUID(payload["member_id"]))
        elif event_type == "conversation.closed.v1":
            self.closed_conversations.add((org, UUID(payload["conversation_id"])))
        elif event_type == "device.revoked.v1":
            for token in self.tokens.values():
                if token.organization_id == org and token.device_id == UUID(payload["device_id"]):
                    token.enabled = False
        elif event_type != "message.created.v1":
            return False
        else:
            conversation, sender = (
                UUID(payload["conversation_id"]),
                UUID(payload["sender_member_id"]),
            )
            projection = self.memberships.get((org, conversation))
            if not projection or (org, conversation) in self.closed_conversations:
                return False
            for member in projection["members"] - {sender}:
                pref = self.preferences.get((org, member), Preference())
                if not pref.push_enabled or not pref.message_notifications:
                    continue
                notification_id = uuid4()
                self.notifications.append(
                    (
                        notification_id,
                        org,
                        member,
                        self._payload(
                            pref, payload.get("sender_name", "New message"), payload.get("body", "")
                        ),
                    )
                )
                for token in self.tokens.values():
                    if token.organization_id == org and token.member_id == member and token.enabled:
                        if not any(
                            d.notification_id == notification_id and d.token_id == token.id
                            for d in self.deliveries
                        ):
                            self.deliveries.append(Delivery(uuid4(), notification_id, token.id))
        self.processed_events.add(event_id)
        return True

    async def send_pending(self):
        semaphore = asyncio.Semaphore(self.max_concurrent_sends)

        async def send(delivery):
            if (
                delivery.status not in {"PENDING", "RETRY_PENDING"}
                or delivery.attempt_count >= self.max_attempts
            ):
                return
            token = self.tokens.get(delivery.token_id)
            if not token or not token.enabled:
                delivery.status = "CANCELLED"
                return
            async with semaphore:
                delivery.attempt_count += 1
                result: ProviderResult = await self.provider.send(token, {})
            if result.success:
                delivery.status = "SENT"
                self.outbox.append(
                    {
                        "event_type": "notification.sent.v1",
                        "organization_id": str(token.organization_id),
                    }
                )
            elif result.token_invalid:
                token.enabled = False
                token.invalidated_at = now()
                delivery.status = "CANCELLED"
                self.outbox.append(
                    {
                        "event_type": "push_token.invalidated.v1",
                        "organization_id": str(token.organization_id),
                    }
                )
            elif result.retryable and delivery.attempt_count < self.max_attempts:
                delivery.status = "RETRY_PENDING"
                delivery.next_attempt_at = now() + timedelta(seconds=2**delivery.attempt_count)
            else:
                delivery.status, delivery.error_code = "FAILED", result.error_code
                self.outbox.append(
                    {
                        "event_type": "notification.failed.v1",
                        "organization_id": str(token.organization_id),
                    }
                )

        await asyncio.gather(*(send(delivery) for delivery in self.deliveries))
