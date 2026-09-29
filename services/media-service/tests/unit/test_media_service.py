from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.events import rabbit_callback
from app.schemas import UploadRequest
from app.security import Principal
from app.service import MediaService, OutboxPublisher, safe_filename, timestamp
from app.storage import FakePrivateStorage, ObjectInfo


def context():
    org, conversation = uuid4(), uuid4()
    return Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation})), conversation


def request(conversation, **changes):
    values = {
        "conversation_id": conversation,
        "filename": "photo.jpg",
        "mime_type": "image/jpeg",
        "size_bytes": 5,
        "media_type": "image",
    }
    values.update(changes)
    return UploadRequest(**values)


@pytest.mark.asyncio
async def test_initiate_generates_private_key_and_sanitizes_filename():
    principal, conversation = context()
    service = MediaService(FakePrivateStorage())
    result = await service.initiate(principal, request(conversation, filename="../../evil?.jpg"))
    media = service.media[result["media_id"]]
    assert result["upload_url"].startswith("https://private.invalid/upload/")
    assert media.safe_filename == "evil_.jpg"
    assert (
        f"organizations/{principal.organization_id}/conversations/{conversation}/media/{media.id}/original"
        in media.object_key
    )
    assert "evil" not in media.object_key


@pytest.mark.asyncio
async def test_mime_and_size_policy_are_enforced():
    principal, conversation = context()
    service = MediaService(FakePrivateStorage())
    with pytest.raises(HTTPException, match="unsupported"):
        await service.initiate(
            principal, request(conversation, mime_type="application/x-msdownload")
        )
    with pytest.raises(HTTPException, match="size limit"):
        await service.initiate(principal, request(conversation, size_bytes=11 * 1024 * 1024))


@pytest.mark.asyncio
async def test_complete_verifies_object_is_idempotent_and_accounts_storage():
    principal, conversation = context()
    storage, service = FakePrivateStorage(), MediaService(FakePrivateStorage())
    service.storage = storage
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    storage.objects[(media.bucket, media.object_key)] = ObjectInfo(5, "image/jpeg")
    assert (await service.complete(principal, media.id)).status == "READY"
    assert (await service.complete(principal, media.id)).status == "READY"
    assert service.usage[principal.organization_id] == {
        "stored_bytes": 5,
        "media_count": 1,
        "reserved_bytes": 0,
    }
    assert [event["event_type"] for event in service.outbox] == ["media.ready.v1"]


@pytest.mark.asyncio
async def test_completion_fails_when_storage_object_is_wrong():
    principal, conversation = context()
    storage, service = FakePrivateStorage(), MediaService(FakePrivateStorage())
    service.storage = storage
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    storage.objects[(media.bucket, media.object_key)] = ObjectInfo(6, "image/jpeg")
    with pytest.raises(HTTPException, match="verification"):
        await service.complete(principal, media.id)
    assert media.status == "FAILED"


@pytest.mark.asyncio
async def test_private_download_and_deletion_remove_original_and_thumbnail():
    principal, conversation = context()
    storage, service = FakePrivateStorage(), MediaService(FakePrivateStorage())
    service.storage = storage
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    storage.objects[(media.bucket, media.object_key)] = ObjectInfo(5, "image/jpeg")
    await service.complete(principal, media.id)
    media.thumbnail_object_key = media.object_key.replace("original", "thumbnail")
    storage.objects[(media.bucket, media.thumbnail_object_key)] = ObjectInfo(2, "image/jpeg")
    assert (await service.download(principal, media.id)).startswith(
        "https://private.invalid/download/"
    )
    await service.delete(principal, media.id)
    await service.delete(principal, media.id)
    assert media.status == "DELETED" and len(storage.deleted) == 2
    with pytest.raises(HTTPException, match="unavailable"):
        await service.download(principal, media.id)


@pytest.mark.asyncio
async def test_reference_consumer_is_idempotent_and_orphan_cleanup_is_safe():
    principal, conversation = context()
    storage, service = FakePrivateStorage(), MediaService(FakePrivateStorage())
    service.storage = storage
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    created = {
        "event_id": "event-1",
        "event_type": "message.created.v1",
        "organization_id": str(principal.organization_id),
        "payload": {"media_id": str(media.id), "message_id": str(uuid4())},
    }
    assert await service.consume_message_event(created)
    assert not await service.consume_message_event(created)
    media.created_at = timestamp() - timedelta(hours=2)
    assert await service.cleanup_orphans() == []
    deleted = {**created, "event_id": "event-2", "event_type": "message.deleted.v1"}
    assert await service.consume_message_event(deleted)
    assert await service.cleanup_orphans() == [media.id]


@pytest.mark.asyncio
async def test_outbox_marks_published_only_after_publish_succeeds():
    principal, conversation = context()
    service = MediaService(FakePrivateStorage())
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    service._event("media.ready.v1", media, "correlation")
    published = []

    async def publish(event):
        published.append(event)

    await OutboxPublisher(service, publish).publish_pending()
    assert published[0]["correlation_id"] == "correlation"
    assert service.outbox[0]["status"] == "PUBLISHED"


@pytest.mark.asyncio
async def test_storage_failure_keeps_event_pending_for_retry():
    principal, conversation = context()
    storage = FakePrivateStorage()
    service = MediaService(storage)
    result = await service.initiate(principal, request(conversation))
    media = service.media[result["media_id"]]
    service._event("media.ready.v1", media)

    async def failing_publish(_event):
        raise RuntimeError("broker unavailable")

    with pytest.raises(RuntimeError):
        await OutboxPublisher(service, failing_publish).publish_pending()
    assert service.outbox[0]["status"] == "PENDING"


def test_rabbit_reference_consumer_acks_after_processing_and_nacks_failure():
    calls = []

    class Channel:
        def basic_ack(self, tag):
            calls.append(("ack", tag))

        def basic_nack(self, tag, requeue):
            calls.append(("nack", tag, requeue))

    class Method:
        delivery_tag = 7

    class Consumer:
        async def consume_message_event(self, _event):
            calls.append(("processed", 7))

    rabbit_callback(Consumer(), Channel(), Method(), None, b'{"event_id": "event"}')
    assert calls == [("processed", 7), ("ack", 7)]

    class FailingConsumer:
        async def consume_message_event(self, _event):
            raise RuntimeError("retry")

    rabbit_callback(FailingConsumer(), Channel(), Method(), None, b"{}")
    assert calls[-1] == ("nack", 7, True)


def test_filename_sanitization_blocks_path_traversal():
    assert safe_filename("..\\..\\bad/../file?.pdf") == "file_.pdf"
