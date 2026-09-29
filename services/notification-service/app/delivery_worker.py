"""Persistent, provider-agnostic NotificationDelivery worker."""

import asyncio
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from app.config import get_settings
from app.db import SessionLocal, engine
from app.providers import FakePushProvider, FirebaseFCMProvider, ProviderResult, ProviderRouter
from app.repositories import (
    NotificationDeliveryRepository,
    NotificationRepository,
    OutboxRepository,
    PushTokenRepository,
)


@dataclass(frozen=True)
class ClaimedDelivery:
    id: object
    organization_id: object
    claimed_at: datetime


@dataclass(frozen=True)
class DeliveryContext:
    delivery: object
    token: object | None
    notification: object | None


class DeliveryWorker:
    def __init__(
        self,
        providers,
        session_factory=SessionLocal,
        *,
        batch_size=100,
        max_attempts=3,
        retry_base_seconds=2,
        retry_max_seconds=300,
        stale_after_seconds=300,
    ):
        self.providers = providers
        self.session_factory = session_factory
        self.batch_size = batch_size
        self.max_attempts = max_attempts
        self.retry_base_seconds = retry_base_seconds
        self.retry_max_seconds = retry_max_seconds
        self.stale_after = timedelta(seconds=stale_after_seconds)

    async def claim(self, now=None):
        now = now or datetime.now(UTC)
        async with self.session_factory() as session:
            async with session.begin():
                rows = await NotificationDeliveryRepository(session).claim_batch(
                    now, now - self.stale_after, self.batch_size
                )
                claimed = [ClaimedDelivery(row.id, row.organization_id, now) for row in rows]
        return claimed

    async def run_once(self, now=None):
        claimed = await self.claim(now)
        for delivery in claimed:
            await self._send_and_finalize(delivery, now)
        return len(claimed)

    async def _send_and_finalize(self, claimed, now):
        context = await self._load_context(claimed)
        if context is None:
            return
        if context.token is None or not context.token.enabled:
            await self._finalize(
                claimed,
                ProviderResult(False, error_code="push token unavailable", token_invalid=True),
                now,
            )
            return
        try:
            result = await self.providers.send(
                context.delivery.provider,
                context.token,
                {
                    "notification": {
                        "title": context.notification.title or "",
                        "body": context.notification.body or "",
                    },
                    "data": {
                        "notification_id": str(context.notification.id),
                        "conversation_id": str(context.notification.conversation_id),
                    },
                },
            )
        except Exception as exc:  # Provider boundaries must never strand SENDING deliveries.
            result = ProviderResult(
                False, error_code=f"provider exception: {type(exc).__name__}", retryable=True
            )
        await self._finalize(claimed, result, now)

    async def _load_context(self, claimed):
        async with self.session_factory() as session:
            deliveries = NotificationDeliveryRepository(session)
            delivery = await deliveries.get_by_id(claimed.organization_id, claimed.id)
            if (
                delivery is None
                or delivery.status != "SENDING"
                or delivery.claimed_at != claimed.claimed_at
            ):
                return None
            token = await PushTokenRepository(session).get_by_id(
                claimed.organization_id, delivery.device_push_token_id
            )
            notification = await NotificationRepository(session).get_by_id(
                claimed.organization_id, delivery.notification_id
            )
            return DeliveryContext(delivery, token, notification)

    async def _finalize(self, claimed, result, now):
        async with self.session_factory() as session:
            async with session.begin():
                deliveries = NotificationDeliveryRepository(session)
                delivery = await deliveries.get_by_id(claimed.organization_id, claimed.id)
                if (
                    delivery is None
                    or delivery.status != "SENDING"
                    or delivery.claimed_at != claimed.claimed_at
                ):
                    return False
                delivery.claimed_at = None
                delivery.attempt_count += 1
                if result.success:
                    delivery.status = "SENT"
                    delivery.next_attempt_at = None
                    delivery.last_error = None
                    await self._add_outbox(session, delivery, "notification.sent.v1")
                elif result.token_invalid:
                    delivery.status = "FAILED"
                    delivery.next_attempt_at = None
                    delivery.last_error = self._sanitize_error(result.error_code)
                    await PushTokenRepository(session).disable_by_id(
                        claimed.organization_id, delivery.device_push_token_id
                    )
                    await self._add_outbox(session, delivery, "push_token.invalidated.v1")
                    await self._add_outbox(session, delivery, "notification.failed.v1")
                elif result.retryable and delivery.attempt_count < self.max_attempts:
                    delivery.status = "RETRY_PENDING"
                    delivery.last_error = self._sanitize_error(result.error_code)
                    delivery.next_attempt_at = now + timedelta(
                        seconds=self._backoff_seconds(delivery.attempt_count)
                    )
                else:
                    delivery.status = "FAILED"
                    delivery.next_attempt_at = None
                    delivery.last_error = self._sanitize_error(result.error_code)
                    await self._add_outbox(session, delivery, "notification.failed.v1")
        return True

    def _backoff_seconds(self, attempt_count):
        return min(self.retry_max_seconds, self.retry_base_seconds * (2 ** (attempt_count - 1)))

    @staticmethod
    def _sanitize_error(error):
        if not error:
            return "provider delivery failed"
        text = str(error)[:512]
        if re.search(
            r"authorization|bearer|password|secret|private.?key|jwt|token\s*[:=]",
            text,
            flags=re.IGNORECASE,
        ):
            return "provider delivery failed"
        return re.sub(r"[^a-zA-Z0-9 .:_-]", "_", text)

    async def _add_outbox(self, session, delivery, event_type):
        event_id = uuid5(NAMESPACE_URL, f"{event_type}:{delivery.organization_id}:{delivery.id}")
        outbox = OutboxRepository(session)
        if await outbox.get_by_event_id(event_id) is None:
            await outbox.add(
                event_id=event_id,
                organization_id=delivery.organization_id,
                event_type=event_type,
                status="PENDING",
                payload={
                    "delivery_id": str(delivery.id),
                    "notification_id": str(delivery.notification_id),
                },
            )


def build_provider_router():
    settings = get_settings()
    if settings.push_provider == "fcm":
        return ProviderRouter({"FCM": FirebaseFCMProvider(settings.firebase_credentials_json)})
    return ProviderRouter({"FCM": FakePushProvider()})


async def run_forever(worker: DeliveryWorker, poll_seconds: float) -> None:
    try:
        while True:
            await worker.run_once()
            await asyncio.sleep(poll_seconds)
    finally:
        await engine.dispose()


def main() -> None:
    settings = get_settings()
    worker = DeliveryWorker(build_provider_router())
    try:
        asyncio.run(run_forever(worker, settings.delivery_poll_seconds))
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
