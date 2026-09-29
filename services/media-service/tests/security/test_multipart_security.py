from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.schemas import UploadRequest
from app.security import Principal
from app.service import MediaService
from app.storage import FakePrivateStorage


@pytest.mark.asyncio
async def test_cross_tenant_multipart_operations_are_hidden_and_oversize_is_rejected():
    org, conversation = uuid4(), uuid4()
    owner = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    service = MediaService(FakePrivateStorage())
    request = UploadRequest(
        conversation_id=conversation,
        filename="large.mp4",
        mime_type="video/mp4",
        size_bytes=32 * 1024 * 1024,
        media_type="video",
    )
    result = await service.initiate_multipart(owner, request)
    intruder = Principal(uuid4(), uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    for name, action in (
        ("parts", service.multipart_part_urls),
        ("status", service.multipart_status),
        ("complete", service.complete_multipart),
        ("abort", service.abort_multipart),
    ):
        with pytest.raises(HTTPException) as error:
            if name == "parts":
                await action(intruder, result["media_id"], [1])
            elif name == "complete":
                await action(intruder, result["media_id"], [])
            else:
                await action(intruder, result["media_id"])
        assert error.value.status_code == 404
    with pytest.raises(HTTPException):
        await service.initiate_multipart(
            owner, request.model_copy(update={"size_bytes": 5 * 1024**3 + 1})
        )
