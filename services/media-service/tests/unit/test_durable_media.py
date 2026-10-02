from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import MediaPolicy
from app.durable import DurableMediaService
from app.models import (
    Base,
    Media,
    MediaReference,
    OrganizationStorageUsage,
    OutboxEvent,
    ProcessedEvent,
)
from app.schemas import UploadRequest
from app.security import Principal
from app.storage import FakePrivateStorage, ObjectInfo, StorageError


@pytest.fixture
async def durable(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path / 'media.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    yield DurableMediaService(FakePrivateStorage(), MediaPolicy(), sessions), sessions
    await engine.dispose()


def context():
    organization_id, conversation_id = uuid4(), uuid4()
    principal = Principal(organization_id, uuid4(), uuid4(), uuid4(), frozenset({conversation_id}))
    request = UploadRequest(
        conversation_id=conversation_id,
        filename="photo.jpg",
        mime_type="image/jpeg",
        size_bytes=5,
        media_type="image",
    )
    return principal, request


@pytest.mark.asyncio
async def test_metadata_usage_and_outbox_survive_reconstruction(durable):
    service, sessions = durable
    principal, request = context()
    initiated = await service.initiate(principal, request, "correlation")
    key = (service.policy.bucket, initiated["object_key"])
    service.storage.objects[key] = ObjectInfo(5, "image/jpeg")
    rebuilt = DurableMediaService(service.storage, service.policy, sessions)
    media = await rebuilt.complete(principal, initiated["media_id"], "correlation")
    async with sessions() as session:
        assert await session.get(Media, media.id)
        usage = await session.get(OrganizationStorageUsage, principal.organization_id)
        assert (usage.stored_bytes, usage.media_count) == (5, 1)
        assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 1


@pytest.mark.asyncio
async def test_processed_event_and_reference_are_durable_and_idempotent(durable):
    service, sessions = durable
    principal, request = context()
    media_id = (await service.initiate(principal, request))["media_id"]
    event = {
        "event_id": str(uuid4()),
        "event_type": "message.created.v1",
        "organization_id": str(principal.organization_id),
        "payload": {"media_id": str(media_id), "message_id": str(uuid4())},
    }
    assert await service.consume_message_event(event)
    rebuilt = DurableMediaService(service.storage, service.policy, sessions)
    assert not await rebuilt.consume_message_event(event)
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(ProcessedEvent)) == 1
        assert await session.scalar(select(func.count()).select_from(MediaReference)) == 1


@pytest.mark.asyncio
async def test_failed_mutation_does_not_persist_partial_state(durable):
    service, sessions = durable
    principal, request = context()

    async def fail(*_args):
        raise StorageError("storage unavailable")

    service.storage.presign_upload = fail
    with pytest.raises(HTTPException):
        await service.initiate(principal, request)
    async with sessions() as session:
        assert await session.scalar(select(func.count()).select_from(Media)) == 0
        assert await session.scalar(select(func.count()).select_from(OutboxEvent)) == 0
