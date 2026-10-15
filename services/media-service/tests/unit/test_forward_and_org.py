from datetime import timedelta
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas import UploadRequest
from app.security import Principal
from app.service import MediaService, timestamp
from app.storage import FakePrivateStorage, ObjectInfo


def org_context():
    org, original, forwarded = uuid4(), uuid4(), uuid4()
    owner = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({original, forwarded}))
    peer = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({forwarded}))
    return org, original, forwarded, owner, peer


@pytest.mark.asyncio
async def test_forwarded_media_authorizes_target_conversation_not_original_only():
    org, original, forwarded, owner, peer = org_context()
    service = MediaService(FakePrivateStorage())
    result = await service.initiate(
        owner,
        UploadRequest(
            conversation_id=original,
            filename="clip.webm",
            mime_type="video/webm",
            size_bytes=10,
            media_type="video",
        ),
    )
    media = service.media[result["media_id"]]
    service.storage.objects[(media.bucket, media.object_key)] = ObjectInfo(10, "video/webm")
    await service.complete(owner, media.id)
    service.references.add((media.id, str(uuid4()), forwarded))
    media.reference_count = 1

    assert await service.download(peer, media.id)
    intruder = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({original}))
    with pytest.raises(HTTPException) as error:
        await service.download(intruder, media.id)
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_revoked_member_cannot_upload_company_media():
    org, conversation = uuid4(), uuid4()
    member = uuid4()
    principal = Principal(org, uuid4(), member, uuid4(), frozenset({conversation}))
    service = MediaService(FakePrivateStorage())
    service.org_membership.revoke(org, member)
    with pytest.raises(HTTPException) as error:
        await service.initiate(
            principal,
            UploadRequest(
                conversation_id=conversation,
                filename="a.jpg",
                mime_type="image/jpeg",
                size_bytes=1,
                media_type="image",
            ),
        )
    assert error.value.status_code == 403


@pytest.mark.asyncio
async def test_personal_media_unaffected_by_org_revocation():
    conversation = uuid4()
    principal = Principal(None, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    service = MediaService(FakePrivateStorage())
    service.org_membership.revoke(uuid4(), uuid4())
    result = await service.initiate(
        principal,
        UploadRequest(
            conversation_id=conversation,
            filename="a.jpg",
            mime_type="image/jpeg",
            size_bytes=1,
            media_type="image",
        ),
    )
    assert result["media_id"]


@pytest.mark.asyncio
async def test_voice_note_uses_audio_mimes_with_smaller_limit():
    conversation = uuid4()
    principal = Principal(None, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    service = MediaService(FakePrivateStorage())
    await service.initiate(
        principal,
        UploadRequest(
            conversation_id=conversation,
            filename="note.webm",
            mime_type="audio/webm",
            size_bytes=100,
            media_type="voice",
        ),
    )


@pytest.mark.asyncio
async def test_checksum_verified_on_complete():
    org, conversation = uuid4(), uuid4()
    principal = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    storage, service = FakePrivateStorage(), MediaService(FakePrivateStorage())
    service.storage = storage
    checksum = "a" * 64
    result = await service.initiate(
        principal,
        UploadRequest(
            conversation_id=conversation,
            filename="a.jpg",
            mime_type="image/jpeg",
            size_bytes=5,
            media_type="image",
            checksum_sha256=checksum,
        ),
    )
    media = service.media[result["media_id"]]
    storage.objects[(media.bucket, media.object_key)] = ObjectInfo(
        5, "image/jpeg", checksum_sha256=checksum
    )
    await service.complete(principal, media.id)
    media2 = service.media[
        (
            await service.initiate(
                principal,
                UploadRequest(
                    conversation_id=conversation,
                    filename="b.jpg",
                    mime_type="image/jpeg",
                    size_bytes=5,
                    media_type="image",
                    checksum_sha256=checksum,
                ),
            )
        )["media_id"]
    ]
    storage.objects[(media2.bucket, media2.object_key)] = ObjectInfo(
        5, "image/jpeg", checksum_sha256="b" * 64
    )
    with pytest.raises(HTTPException, match="checksum"):
        await service.complete(principal, media2.id)


@pytest.mark.asyncio
async def test_unreferenced_ready_media_is_garbage_collected():
    org, conversation = uuid4(), uuid4()
    principal = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    storage = FakePrivateStorage()
    service = MediaService(storage)
    result = await service.initiate(
        principal,
        UploadRequest(
            conversation_id=conversation,
            filename="a.jpg",
            mime_type="image/jpeg",
            size_bytes=5,
            media_type="image",
        ),
    )
    media = service.media[result["media_id"]]
    service.storage.objects[(media.bucket, media.object_key)] = ObjectInfo(5, "image/jpeg")
    await service.complete(principal, media.id)
    media.uploaded_at = timestamp() - timedelta(days=8)
    cleaned = await service.cleanup_unreferenced_ready()
    assert cleaned == [media.id]
    assert media.status == "DELETED"
