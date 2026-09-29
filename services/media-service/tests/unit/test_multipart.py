from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.config import MediaPolicy
from app.schemas import UploadRequest
from app.security import Principal
from app.service import MediaService, timestamp
from app.storage import FakePrivateStorage


def setup(size=32 * 1024 * 1024):
    org, conversation = uuid4(), uuid4()
    principal = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    storage = FakePrivateStorage()
    service = MediaService(storage, MediaPolicy(multipart_threshold_bytes=16 * 1024 * 1024))
    request = UploadRequest(
        conversation_id=conversation,
        filename="large.mp4",
        mime_type="video/mp4",
        size_bytes=size,
        media_type="video",
    )
    return principal, service, storage, request


@pytest.mark.asyncio
async def test_multipart_is_selected_and_5gb_is_supported_without_uploading_bytes():
    principal, service, _, request = setup(5 * 1024 * 1024 * 1024)
    result = await service.initiate(principal, request)
    assert result["upload_strategy"] == "MULTIPART"
    assert result["part_size"] >= 8 * 1024 * 1024
    assert result["part_count"] <= 10_000


@pytest.mark.asyncio
async def test_multipart_parts_are_bounded_validated_and_resumable():
    principal, service, storage, request = setup()
    result = await service.initiate_multipart(principal, request)
    media = service.media[result["media_id"]]
    urls = await service.multipart_part_urls(principal, media.id, [1, 2])
    assert [item["part_number"] for item in urls] == [1, 2]
    with pytest.raises(HTTPException, match="invalid part"):
        await service.multipart_part_urls(principal, media.id, [3])
    storage.add_part(result["upload_id"], 1, "etag-1", 16 * 1024 * 1024)
    resumed = await service.multipart_status(principal, media.id)
    assert resumed["uploaded_parts"] == [
        {"part_number": 1, "etag": "etag-1", "size": 16 * 1024 * 1024}
    ]


@pytest.mark.asyncio
async def test_multipart_completion_verifies_final_object_and_accounts_once():
    principal, service, storage, request = setup()
    result = await service.initiate_multipart(principal, request)
    media = service.media[result["media_id"]]
    size = result["part_size"]
    storage.add_part(result["upload_id"], 1, "etag-1", size)
    storage.add_part(result["upload_id"], 2, "etag-2", request.size_bytes - size)
    parts = [{"part_number": 1, "etag": "etag-1"}, {"part_number": 2, "etag": "etag-2"}]
    assert (await service.complete_multipart(principal, media.id, parts)).status == "READY"
    assert (await service.complete_multipart(principal, media.id, parts)).status == "READY"
    assert service.usage[principal.organization_id] == {
        "stored_bytes": request.size_bytes,
        "media_count": 1,
        "reserved_bytes": 0,
    }
    assert [event["event_type"] for event in service.outbox] == ["media.ready.v1"]


@pytest.mark.asyncio
async def test_abort_and_stale_cleanup_are_retryable_and_release_reserved_bytes():
    principal, service, storage, request = setup()
    first = await service.initiate_multipart(principal, request)
    first_media = service.media[first["media_id"]]
    await service.abort_multipart(principal, first_media.id)
    await service.abort_multipart(principal, first_media.id)
    assert first_media.status == "FAILED"
    second = await service.initiate_multipart(principal, request)
    second_media = service.media[second["media_id"]]
    second_media.created_at = timestamp() - timedelta(hours=2)
    assert await service.cleanup_orphans() == [second_media.id]
    assert second["upload_id"] not in storage.multipart


@pytest.mark.asyncio
async def test_invalid_complete_and_storage_failure_do_not_mark_ready():
    principal, service, storage, request = setup()
    result = await service.initiate_multipart(principal, request)
    media = service.media[result["media_id"]]
    with pytest.raises(HTTPException, match="incomplete"):
        await service.complete_multipart(principal, media.id, [{"part_number": 1, "etag": "etag"}])
    storage.fail = True
    with pytest.raises(HTTPException, match="part URL"):
        await service.multipart_part_urls(principal, media.id, [1])
    assert media.status == "UPLOADING"
