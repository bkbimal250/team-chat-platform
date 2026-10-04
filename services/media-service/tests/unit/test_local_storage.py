import json
from datetime import datetime, timedelta, timezone

import pytest

from app.local_storage import LocalPrivateStorage
from app.storage import StorageError


@pytest.mark.asyncio
async def test_signed_private_storage_is_tenant_scoped(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path), "s" * 32, "http://localhost:8005")
    expires = datetime.now(timezone.utc) + timedelta(minutes=5)
    url, headers, _ = await storage.presign_upload("tenant-a", "private", "image/png", expires)
    token = url.rsplit("/", 1)[1]
    assert storage.verify(token, "put")["bucket"] == "tenant-a"
    with pytest.raises(StorageError):
        storage.verify(token, "get")
    with pytest.raises(StorageError):
        storage.verify(token + "bad", "put")
    path = storage.location("tenant-a", "private")
    assert path.parent == tmp_path
    path.write_bytes(b"image")
    path.with_suffix(".json").write_text(json.dumps({"mime": "image/png"}))
    assert (await storage.head("tenant-a", "private")).size_bytes == 5
    assert await storage.head("tenant-b", "private") is None
    await storage.delete("tenant-a", "private")
    assert await storage.head("tenant-a", "private") is None


@pytest.mark.asyncio
async def test_expired_capability_is_rejected(tmp_path):
    storage = LocalPrivateStorage(str(tmp_path), "s" * 32, "http://localhost")
    token = storage.capability("get", "bucket", "key", -1).rsplit("/", 1)[1]
    with pytest.raises(StorageError):
        storage.verify(token, "get")
