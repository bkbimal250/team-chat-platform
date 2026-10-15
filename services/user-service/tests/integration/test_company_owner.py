import asyncio
import os
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.events import consume
from app.main import Base, OutboxEvent, User, UserPreferences, app, db


@pytest.mark.parametrize(
    "path", ["/internal/v1/users/company-owner", "/internal/v1/users/provision"]
)
def test_owner_profile_retry_and_identity_event_do_not_duplicate(monkeypatch, path):
    asyncio.run(run_owner_profile_test(monkeypatch, path))


async def run_owner_profile_test(monkeypatch, path):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with sessions() as session:
            yield session

    app.dependency_overrides[db] = dependency
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "test-internal")
    identity_id = uuid4()
    payload = {"identity_id": str(identity_id), "display_name": "Owner Profile"}
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (
                await client.post(path, json=payload, headers={"X-Internal-Service-Token": "wrong"})
            ).status_code == 401
            headers = {"X-Internal-Service-Token": "test-internal"}
            first = await client.post(path, json=payload, headers=headers)
            second = await client.post(
                path, json={**payload, "display_name": "Do not overwrite"}, headers=headers
            )
            assert first.status_code == 200 and first.json() == second.json()
        async with sessions.begin() as session:
            event = {
                "event_id": str(uuid4()),
                "event_type": "identity.created.v1",
                "producer": "identity",
                "payload": {"identity_id": str(identity_id)},
            }
            assert await consume(session, event)
            assert not await consume(session, event)
        async with sessions() as session:
            assert (
                await session.scalar(
                    select(func.count()).select_from(User).where(User.identity_id == identity_id)
                )
                == 1
            )
            user = await session.scalar(select(User).where(User.identity_id == identity_id))
            assert user.display_name == "Owner Profile"
            assert await session.get(UserPreferences, user.id)
            assert (
                await session.scalar(
                    select(func.count())
                    .select_from(OutboxEvent)
                    .where(OutboxEvent.aggregate_id == user.id)
                )
                == 1
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
