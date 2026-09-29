import json
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

from app.db import SessionLocal, engine
from app.models import (
    ConversationMemberProjection,
    ConversationProjection,
    GlobalUserProjection,
    MembershipProjection,
    ProcessedEvent,
    UserProjection,
)
from app.projection_consumers import ProjectionConsumer, UnsupportedProjectionEvent
from app.rabbit import consume_projection_delivery


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    yield
    await engine.dispose()


def event(event_type, payload, organization_id=None):
    return {
        "event_id": str(uuid4()),
        "event_type": event_type,
        "event_version": 2 if event_type.startswith("member.") else 1,
        "organization_id": str(organization_id) if organization_id else None,
        "correlation_id": "projection-test",
        "payload": payload,
    }


def membership_event(kind, organization_id, member_id, user_id, status):
    return event(
        f"member.{kind}.v2",
        {
            "member_id": str(member_id),
            "user_id": str(user_id),
            "status": status,
            "participant_kind": "HUMAN",
        },
        organization_id,
    )


async def cleanup(*user_ids):
    async with SessionLocal.begin() as session:
        for model in (
            ConversationMemberProjection,
            ConversationProjection,
            UserProjection,
            MembershipProjection,
            GlobalUserProjection,
            ProcessedEvent,
        ):
            if hasattr(model, "user_id"):
                await session.execute(delete(model).where(model.user_id.in_(user_ids)))


@pytest.mark.asyncio
async def test_user_event_first_materializes_tenant_user_after_membership():
    user_id, organization_id, member_id = uuid4(), uuid4(), uuid4()
    consumer = ProjectionConsumer()
    try:
        user_event = event("user.created.v1", {"user_id": str(user_id)})
        assert await consumer.consume(user_event)
        assert not await consumer.consume(user_event)
        assert await consumer.consume(
            membership_event("activated", organization_id, member_id, user_id, "ACTIVE")
        )
        async with SessionLocal() as session:
            assert await session.get(GlobalUserProjection, user_id)
            membership = await session.scalar(
                select(MembershipProjection).where(
                    MembershipProjection.organization_id == organization_id
                )
            )
            tenant_user = await session.scalar(
                select(UserProjection).where(UserProjection.organization_id == organization_id)
            )
            assert membership.member_id == member_id
            assert tenant_user.user_id == user_id and tenant_user.status == "ACTIVE"
    finally:
        await cleanup(user_id)


@pytest.mark.asyncio
async def test_membership_first_and_multi_organization_user_are_isolated():
    user_id, member_id, org_a, org_b = uuid4(), uuid4(), uuid4(), uuid4()
    consumer = ProjectionConsumer()
    try:
        assert await consumer.consume(
            membership_event("created", org_a, member_id, user_id, "ACTIVE")
        )
        assert await consumer.consume(
            membership_event("created", org_b, member_id, user_id, "ACTIVE")
        )
        async with SessionLocal() as session:
            assert not (
                await session.scalars(
                    select(UserProjection).where(UserProjection.user_id == user_id)
                )
            ).all()
        assert await consumer.consume(event("user.profile_updated.v1", {"user_id": str(user_id)}))
        async with SessionLocal() as session:
            rows = (
                await session.scalars(
                    select(UserProjection).where(UserProjection.user_id == user_id)
                )
            ).all()
            assert {row.organization_id for row in rows} == {org_a, org_b}
            assert (
                len(
                    (
                        await session.scalars(
                            select(MembershipProjection).where(
                                MembershipProjection.user_id == user_id
                            )
                        )
                    ).all()
                )
                == 2
            )
    finally:
        await cleanup(user_id)


@pytest.mark.asyncio
async def test_membership_lifecycle_updates_recipient_status_without_duplicate_rows():
    user_id, organization_id, member_id = uuid4(), uuid4(), uuid4()
    consumer = ProjectionConsumer()
    try:
        await consumer.consume(event("user.created.v1", {"user_id": str(user_id)}))
        for kind, status in (
            ("created", "INVITED"),
            ("updated", "ACTIVE"),
            ("activated", "ACTIVE"),
            ("suspended", "SUSPENDED"),
            ("role_changed", "SUSPENDED"),
            ("left", "LEFT"),
            ("removed", "REMOVED"),
        ):
            await consumer.consume(
                membership_event(kind, organization_id, member_id, user_id, status)
            )
        async with SessionLocal() as session:
            membership = await session.scalar(
                select(MembershipProjection).where(
                    MembershipProjection.organization_id == organization_id
                )
            )
            tenant_user = await session.scalar(
                select(UserProjection).where(UserProjection.organization_id == organization_id)
            )
            assert membership.status == tenant_user.status == "REMOVED"
            assert (
                len(
                    (
                        await session.scalars(
                            select(MembershipProjection).where(
                                MembershipProjection.user_id == user_id
                            )
                        )
                    ).all()
                )
                == 1
            )
    finally:
        await cleanup(user_id)


@pytest.mark.asyncio
async def test_conversation_lifecycle_and_member_updates_are_tenant_scoped():
    user_id, member_id, conversation_id, org_a, org_b = uuid4(), uuid4(), uuid4(), uuid4(), uuid4()
    consumer = ProjectionConsumer()
    payload = {
        "conversation_id": str(conversation_id),
        "type": "GROUP",
        "status": "ACTIVE",
        "members": [
            {
                "member_id": str(member_id),
                "user_id": str(user_id),
                "participant_kind": "HUMAN",
                "status": "ACTIVE",
            }
        ],
    }
    try:
        await consumer.consume(event("conversation.created.v1", payload, org_a))
        await consumer.consume(event("conversation.created.v1", payload, org_b))
        payload |= {
            "member_id": str(member_id),
            "user_id": str(user_id),
            "resulting_status": "ACTIVE",
        }
        await consumer.consume(event("conversation.member_role_changed.v1", payload, org_a))
        payload |= {
            "member_id": str(member_id),
            "user_id": str(user_id),
            "resulting_status": "LEFT",
        }
        await consumer.consume(event("conversation.member_left.v1", payload, org_a))
        async with SessionLocal() as session:
            left = await session.scalar(
                select(ConversationMemberProjection).where(
                    ConversationMemberProjection.organization_id == org_a,
                    ConversationMemberProjection.conversation_id == conversation_id,
                )
            )
            active = await session.scalar(
                select(ConversationMemberProjection).where(
                    ConversationMemberProjection.organization_id == org_b,
                    ConversationMemberProjection.conversation_id == conversation_id,
                )
            )
            assert left.status == "LEFT" and active.status == "ACTIVE"
        await consumer.consume(
            event("conversation.closed.v1", payload | {"status": "CLOSED"}, org_a)
        )
    finally:
        await cleanup(user_id)


@pytest.mark.asyncio
async def test_failed_or_unsupported_projection_events_do_not_persist_partial_state():
    user_id, organization_id, member_id = uuid4(), uuid4(), uuid4()
    consumer = ProjectionConsumer()
    malformed = membership_event("created", organization_id, member_id, user_id, "ACTIVE")
    del malformed["payload"]["status"]
    try:
        with pytest.raises(UnsupportedProjectionEvent):
            await consumer.consume(malformed)
        async with SessionLocal() as session:
            assert not await session.scalar(
                select(MembershipProjection).where(MembershipProjection.user_id == user_id)
            )
            assert not await session.scalar(
                select(ProcessedEvent).where(ProcessedEvent.event_id == malformed["event_id"])
            )
        unsupported = event("user.created.v1", {"user_id": str(user_id)})
        unsupported["event_version"] = 2
        with pytest.raises(UnsupportedProjectionEvent):
            await consumer.consume(unsupported)
    finally:
        await cleanup(user_id)


@pytest.mark.asyncio
async def test_projection_delivery_acks_after_consumer_and_nacks_failures():
    class Channel:
        def __init__(self):
            self.calls = []

        def basic_ack(self, delivery_tag):
            self.calls.append(("ack", delivery_tag))

        def basic_nack(self, delivery_tag, requeue):
            self.calls.append(("nack", delivery_tag, requeue))

    class Consumer:
        async def consume(self, _):
            channel.calls.append(("commit", 1))

    class FailingConsumer:
        async def consume(self, _):
            raise RuntimeError("database failure")

    channel = Channel()
    await consume_projection_delivery(Consumer(), channel, 1, json.dumps({}).encode())
    await consume_projection_delivery(FailingConsumer(), channel, 2, json.dumps({}).encode())
    assert channel.calls == [("commit", 1), ("ack", 1), ("nack", 2, True)]
