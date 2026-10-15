from uuid import uuid4

import pytest

from app.db import SessionLocal, engine
from app.repositories import PreferenceRepository


async def transaction():
    session = SessionLocal()
    await session.begin()
    return session


@pytest.fixture(autouse=True)
async def dispose_engine_after_test():
    await engine.dispose(close=False)
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_preferences_are_scoped_by_organization_and_member():
    session, organization_a, organization_b, member_id = (
        await transaction(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    try:
        repository = PreferenceRepository(session)
        preference_a = await repository.upsert(
            organization_a, member_id, push_enabled=False, preview="HIDDEN"
        )
        preference_b = await repository.upsert(
            organization_b, member_id, push_enabled=True, preview="FULL"
        )
        assert await repository.get(organization_a, member_id) is preference_a
        assert await repository.get(organization_b, member_id) is preference_b
        assert preference_a.id != preference_b.id
        assert not preference_a.push_enabled and preference_a.preview == "HIDDEN"
        assert preference_b.push_enabled and preference_b.preview == "FULL"
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_tenant_scoped_upsert_does_not_mutate_another_organization():
    session, organization_a, organization_b, member_id = (
        await transaction(),
        uuid4(),
        uuid4(),
        uuid4(),
    )
    try:
        repository = PreferenceRepository(session)
        await repository.upsert(organization_a, member_id, push_enabled=True, preview="FULL")
        await repository.upsert(organization_b, member_id, push_enabled=True, preview="FULL")
        updated = await repository.upsert(
            organization_a, member_id, push_enabled=False, preview="SENDER_ONLY"
        )
        untouched = await repository.get(organization_b, member_id)
        assert not updated.push_enabled and updated.preview == "SENDER_ONLY"
        assert untouched.push_enabled and untouched.preview == "FULL"
    finally:
        await session.rollback()
        await session.close()


@pytest.mark.asyncio
async def test_preference_repository_does_not_commit_uncommitted_changes():
    organization_id, member_id = uuid4(), uuid4()
    session = await transaction()
    try:
        await PreferenceRepository(session).upsert(
            organization_id, member_id, push_enabled=False, preview="HIDDEN"
        )
        assert await PreferenceRepository(session).get(organization_id, member_id)
    finally:
        await session.rollback()
        await session.close()

    verification = SessionLocal()
    try:
        assert await PreferenceRepository(verification).get(organization_id, member_id) is None
    finally:
        await verification.close()


@pytest.mark.asyncio
async def test_personal_preferences_unique_isolated_and_rollback_safe():
    member, other, organization = uuid4(), uuid4(), uuid4()
    session = await transaction()
    try:
        repo = PreferenceRepository(session)
        personal = await repo.upsert(None, member, push_enabled=False, preview="HIDDEN")
        personal_id = personal.id
        workspace = await repo.upsert(organization, member, push_enabled=True)
        assert workspace.id != personal_id
        assert await repo.get(None, other) is None
        await repo.upsert(None, member, push_enabled=True, preview="FULL")
        session.expire_all()
        fresh = await repo.get(None, member)
        assert fresh.id == personal_id
        assert fresh.push_enabled and fresh.preview == "FULL"
        assert (await repo.get(organization, member)).push_enabled
    finally:
        await session.rollback()
        await session.close()
    async with SessionLocal() as verification:
        assert await PreferenceRepository(verification).get(None, member) is None
