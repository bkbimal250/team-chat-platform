"""Leaving a company removes directory access but preserves personal data."""

import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import jwt
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.events import consume
from app.main import (
    Base,
    Contact,
    MembershipProjection,
    User,
    UserBlock,
    UserPreferences,
    UserPrivacySettings,
    app,
    db,
)


def test_member_event_links_user_id_when_profile_arrives_first(monkeypatch):
    asyncio.run(link_order(monkeypatch))


async def link_order(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    org, member, identity_id = uuid4(), uuid4(), uuid4()
    try:
        async with factory.begin() as session:
            assert await consume(
                session,
                {
                    "event_id": str(uuid4()),
                    "event_type": "member.activated.v1",
                    "producer": "organization",
                    "organization_id": str(org),
                    "payload": {"member_id": str(member), "identity_id": str(identity_id)},
                },
            )
        async with factory.begin() as session:
            user = User(id=identity_id, identity_id=identity_id, display_name="Late profile", status="ACTIVE")
            session.add(user)
            await session.flush()
            session.add_all([UserPreferences(user_id=user.id), UserPrivacySettings(user_id=user.id)])
            assert await consume(
                session,
                {
                    "event_id": str(uuid4()),
                    "event_type": "identity.created.v1",
                    "producer": "identity-service",
                    "payload": {"identity_id": str(identity_id), "display_name": "Late profile"},
                },
            )
        async with factory() as session:
            row = await session.scalar(
                select(MembershipProjection).where(
                    MembershipProjection.organization_id == org,
                    MembershipProjection.member_id == member,
                )
            )
            assert row.user_id == identity_id
    finally:
        await engine.dispose()


def test_member_removed_preserves_personal_data(monkeypatch):
    asyncio.run(exercise(monkeypatch))


async def exercise(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with factory() as session:
            yield session

    app.dependency_overrides[db] = dependency
    identity_id, org_id, member_id = uuid4(), uuid4(), uuid4()
    peer_id = uuid4()
    try:
        async with factory.begin() as session:
            user = User(id=identity_id, identity_id=identity_id, display_name="Member", status="ACTIVE")
            peer = User(id=peer_id, identity_id=uuid4(), display_name="Peer", status="ACTIVE")
            session.add_all([user, peer])
            await session.flush()
            session.add_all(
                [
                    UserPreferences(user_id=user.id),
                    UserPrivacySettings(
                        user_id=user.id,
                        profile_photo_visibility="ORGANIZATION",
                        about_visibility="ORGANIZATION",
                    ),
                    Contact(owner_user_id=user.id, phone_digest="digest-member"),
                    UserBlock(blocker_user_id=user.id, blocked_user_id=peer.id),
                    MembershipProjection(
                        organization_id=org_id,
                        member_id=member_id,
                        identity_id=identity_id,
                        user_id=user.id,
                        status="ACTIVE",
                    ),
                ]
            )
        async with factory.begin() as session:
            assert await consume(
                session,
                {
                    "event_id": str(uuid4()),
                    "event_type": "member.removed.v2",
                    "producer": "organization",
                    "organization_id": str(org_id),
                    "payload": {
                        "member_id": str(member_id),
                        "user_id": str(identity_id),
                        "identity_id": str(identity_id),
                        "status": "REMOVED",
                        "resource_id": str(member_id),
                        "changed_fields": ["status"],
                        "participant_kind": "HUMAN",
                    },
                },
            )
        async with factory() as session:
            projection = await session.scalar(
                select(MembershipProjection).where(
                    MembershipProjection.organization_id == org_id,
                    MembershipProjection.member_id == member_id,
                )
            )
            assert projection.status == "REMOVED"
            assert await session.get(User, identity_id) is not None
            assert (
                await session.scalar(select(func.count()).select_from(Contact).where(Contact.owner_user_id == identity_id))
                == 1
            )
            assert (
                await session.scalar(select(func.count()).select_from(UserBlock).where(UserBlock.blocker_user_id == identity_id))
                == 1
            )
            assert await session.get(UserPrivacySettings, identity_id) is not None
            assert await session.get(UserPreferences, identity_id) is not None

        now = datetime.now(UTC)
        claims = {
            "sub": str(identity_id),
            "sid": str(uuid4()),
            "did": str(uuid4()),
            "org": str(org_id),
            "mid": str(member_id),
            "iss": "identity-service",
            "aud": "team-chat-platform",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        token = jwt.encode(claims, os.environ["ACCESS_TOKEN_PRIVATE_KEY"], algorithm="RS256")
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (
                await client.get("/api/v1/users/search?q=Mem", headers={"Authorization": "Bearer " + token})
            ).status_code == 403
            personal = {k: v for k, v in claims.items() if k not in {"org", "mid"}}
            personal_token = jwt.encode(
                personal, os.environ["ACCESS_TOKEN_PRIVATE_KEY"], algorithm="RS256"
            )
            assert (
                await client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + personal_token})
            ).status_code == 200
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
