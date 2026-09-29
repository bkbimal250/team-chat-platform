import asyncio
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import delete, select
from sqlalchemy.dialects import postgresql

from app.db import SessionLocal, engine
from app.delivery_worker import DeliveryWorker
from app.models import DevicePushToken, Notification, NotificationDelivery, OutboxEvent
from app.providers import ProviderResult, ProviderRouter
from app.repositories import NotificationDeliveryRepository, NotificationRepository


class Provider:
    def __init__(self, result=None, error=None, check=None):
        self.result = result or ProviderResult(True)
        self.error = error
        self.check = check
        self.calls = 0

    async def send(self, token, payload):
        self.calls += 1
        if self.check:
            await self.check(token, payload)
        if self.error:
            raise self.error
        return self.result


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


async def seed_delivery(
    organization_id,
    *,
    status="PENDING",
    next_attempt_at=None,
    claimed_at=None,
    attempt_count=0,
    provider="FCM",
    device_id=None,
):
    async with SessionLocal.begin() as session:
        notification = await NotificationRepository(session).create(
            organization_id=organization_id,
            conversation_id=uuid4(),
            message_id=uuid4(),
            recipient_user_id=uuid4(),
            recipient_member_id=uuid4(),
            notification_type="MESSAGE",
            title=None,
            body=None,
            preview_mode="FULL",
        )
        token = DevicePushToken(
            organization_id=organization_id,
            user_id=notification.recipient_user_id,
            member_id=notification.recipient_member_id,
            device_id=device_id or uuid4(),
            platform="IOS",
            provider=provider,
            token=str(uuid4()),
            enabled=True,
        )
        session.add(token)
        await session.flush()
        delivery = await NotificationDeliveryRepository(session).create(
            organization_id=organization_id,
            notification_id=notification.id,
            device_push_token_id=token.id,
            device_id=token.device_id,
            provider=provider,
            status=status,
            attempt_count=attempt_count,
            next_attempt_at=next_attempt_at,
            claimed_at=claimed_at,
        )
        return delivery.id, token.id


async def cleanup(*organization_ids):
    async with SessionLocal.begin() as session:
        for model in (OutboxEvent, NotificationDelivery, Notification, DevicePushToken):
            await session.execute(delete(model).where(model.organization_id.in_(organization_ids)))


@pytest.mark.asyncio
async def test_claims_due_work_with_skip_locked_bounded_batch_and_stale_recovery():
    organization_id, now = uuid4(), datetime.now(UTC)
    pending, _ = await seed_delivery(organization_id)
    due, _ = await seed_delivery(
        organization_id, status="RETRY_PENDING", next_attempt_at=now - timedelta(seconds=1)
    )
    future, _ = await seed_delivery(
        organization_id, status="RETRY_PENDING", next_attempt_at=now + timedelta(seconds=30)
    )
    stale, _ = await seed_delivery(
        organization_id, status="SENDING", claimed_at=now - timedelta(seconds=301)
    )
    recent, _ = await seed_delivery(
        organization_id, status="SENDING", claimed_at=now - timedelta(seconds=1)
    )
    try:
        worker = DeliveryWorker(ProviderRouter({}), batch_size=3, stale_after_seconds=300)
        claimed = await worker.claim(now)
        assert {row.id for row in claimed} <= {pending, due, stale}
        assert len(claimed) == 3
        second = await worker.claim(now)
        assert not second
        async with SessionLocal() as session:
            assert (
                await NotificationDeliveryRepository(session).get_by_id(organization_id, future)
            ).status == "RETRY_PENDING"
            assert (
                await NotificationDeliveryRepository(session).get_by_id(organization_id, recent)
            ).status == "SENDING"
            statement = NotificationDeliveryRepository(session).claim_query(
                now, now - timedelta(seconds=300), 3
            )
            assert "SKIP LOCKED" in str(statement.compile(dialect=postgresql.dialect())).upper()
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_two_workers_do_not_claim_the_same_postgresql_delivery():
    organization_id, now = uuid4(), datetime.now(UTC)
    delivery_id, _ = await seed_delivery(organization_id)
    try:
        router = ProviderRouter({})
        first, second = await asyncio.gather(
            DeliveryWorker(router, batch_size=1).claim(now),
            DeliveryWorker(router, batch_size=1).claim(now),
        )
        claimed = [row.id for rows in (first, second) for row in rows]
        assert claimed == [delivery_id]
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_success_commits_claim_before_provider_io_and_writes_outbox():
    organization_id, now = uuid4(), datetime.now(UTC)
    delivery_id, _ = await seed_delivery(organization_id)

    async def claimed_before_send(_, __):
        async with SessionLocal() as session:
            delivery = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, delivery_id
            )
            assert delivery.status == "SENDING" and delivery.claimed_at is not None

    provider = Provider(ProviderResult(True), check=claimed_before_send)
    try:
        assert await DeliveryWorker(ProviderRouter({"FCM": provider})).run_once(now) == 1
        async with SessionLocal() as session:
            delivery = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, delivery_id
            )
            outbox = await session.scalar(
                select(OutboxEvent).where(OutboxEvent.organization_id == organization_id)
            )
            assert delivery.status == "SENT" and delivery.claimed_at is None
            assert delivery.next_attempt_at is None and delivery.last_error is None
            assert outbox.event_type == "notification.sent.v1"
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_retry_permanent_and_provider_exception_results_are_persisted_safely():
    organization_id, now = uuid4(), datetime.now(UTC)
    retry_id, _ = await seed_delivery(organization_id, provider="RETRY")
    exhausted_id, _ = await seed_delivery(organization_id, provider="EXHAUSTED", attempt_count=2)
    permanent_id, _ = await seed_delivery(organization_id, provider="PERMANENT")
    exception_id, _ = await seed_delivery(organization_id, provider="EXCEPTION")
    router = ProviderRouter(
        {
            "RETRY": Provider(
                ProviderResult(False, error_code="temporary@failure", retryable=True)
            ),
            "EXHAUSTED": Provider(ProviderResult(False, error_code="again", retryable=True)),
            "PERMANENT": Provider(ProviderResult(False, error_code="invalid recipient")),
            "EXCEPTION": Provider(error=RuntimeError("token=secret")),
        }
    )
    try:
        assert await DeliveryWorker(router, batch_size=10, max_attempts=3).run_once(now) == 4
        async with SessionLocal() as session:
            retry = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, retry_id
            )
            exhausted = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, exhausted_id
            )
            permanent = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, permanent_id
            )
            exception = await NotificationDeliveryRepository(session).get_by_id(
                organization_id, exception_id
            )
            assert retry.status == "RETRY_PENDING" and retry.attempt_count == 1
            assert retry.next_attempt_at == now + timedelta(seconds=2)
            assert retry.last_error == "temporary_failure"
            assert exhausted.status == permanent.status == "FAILED"
            assert exception.status == "RETRY_PENDING"
            assert exception.last_error == "provider exception: RuntimeError"
            assert "secret" not in exception.last_error
    finally:
        await cleanup(organization_id)


@pytest.mark.asyncio
async def test_invalid_token_disables_only_the_matching_tenant_token():
    organization_a, organization_b, now, shared_device = (
        uuid4(),
        uuid4(),
        datetime.now(UTC),
        uuid4(),
    )
    delivery_a, token_a = await seed_delivery(organization_a, device_id=shared_device)
    _, token_b = await seed_delivery(
        organization_b,
        status="RETRY_PENDING",
        next_attempt_at=now + timedelta(hours=1),
        device_id=shared_device,
    )
    try:
        provider = Provider(ProviderResult(False, error_code="expired", token_invalid=True))
        await DeliveryWorker(ProviderRouter({"FCM": provider})).run_once(now)
        async with SessionLocal() as session:
            delivery = await NotificationDeliveryRepository(session).get_by_id(
                organization_a, delivery_a
            )
            token_a_row = await session.get(DevicePushToken, token_a)
            token_b_row = await session.get(DevicePushToken, token_b)
            assert delivery.status == "FAILED" and delivery.claimed_at is None
            assert not token_a_row.enabled and token_b_row.enabled
    finally:
        await cleanup(organization_a, organization_b)
