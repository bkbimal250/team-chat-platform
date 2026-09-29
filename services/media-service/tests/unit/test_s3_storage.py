from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import MediaSettings
from app.main import app, build_media_service
from app.schemas import UploadRequest
from app.security import Principal
from app.service import MediaService
from app.storage import S3PrivateStorage, StorageError


class S3Client:
    def __init__(self):
        self.calls = []

    def generate_presigned_url(self, operation, **kwargs):
        self.calls.append((operation, kwargs))
        return f"https://private.example/{operation}"

    def head_object(self, **kwargs):
        self.calls.append(("head_object", kwargs))
        return {"ContentLength": 7, "ContentType": "image/jpeg"}

    def delete_object(self, **kwargs):
        self.calls.append(("delete_object", kwargs))
        return {}

    def head_bucket(self, **kwargs):
        self.calls.append(("head_bucket", kwargs))
        return {}

    def create_multipart_upload(self, **kwargs):
        self.calls.append(("create_multipart_upload", kwargs))
        return {"UploadId": "upload-1"}

    def list_parts(self, **kwargs):
        self.calls.append(("list_parts", kwargs))
        return {"Parts": [{"PartNumber": 1, "ETag": "etag-1", "Size": 7}]}

    def complete_multipart_upload(self, **kwargs):
        self.calls.append(("complete_multipart_upload", kwargs))
        return {}

    def abort_multipart_upload(self, **kwargs):
        self.calls.append(("abort_multipart_upload", kwargs))
        return {}


def s3_settings():
    return MediaSettings(
        app_env="production",
        media_storage_backend="s3",
        aws_region="ap-south-1",
        media_s3_bucket="globalchat-private",
        jwt_public_key="test-public-key",
    )


def test_production_storage_configuration_fails_closed():
    with pytest.raises(ValidationError, match="MEDIA_STORAGE_BACKEND=s3"):
        MediaSettings(app_env="production", media_storage_backend="fake")
    with pytest.raises(ValidationError, match="AWS_REGION"):
        MediaSettings(media_storage_backend="s3", media_s3_bucket="private")
    with pytest.raises(ValidationError, match="MEDIA_S3_BUCKET"):
        MediaSettings(media_storage_backend="s3", aws_region="ap-south-1")
    with pytest.raises(ValidationError, match="JWT_PUBLIC_KEY"):
        MediaSettings(
            app_env="production",
            media_storage_backend="s3",
            aws_region="ap-south-1",
            media_s3_bucket="private",
        )


def test_s3_backend_is_selected_without_static_credentials(monkeypatch):
    calls = []

    class Client:
        pass

    def create_client(*args, **kwargs):
        calls.append((args, kwargs))
        return Client()

    monkeypatch.setattr("app.storage.boto3.client", create_client)
    service = build_media_service(s3_settings())
    assert isinstance(service.storage, S3PrivateStorage)
    assert service.policy.bucket == "globalchat-private"
    assert calls == [(("s3",), {"region_name": "ap-south-1", "endpoint_url": None})]


@pytest.mark.asyncio
async def test_s3_private_operations_presign_and_delete_only_server_owned_keys():
    client = S3Client()
    storage = S3PrivateStorage(region="ap-south-1", bucket="globalchat-private", client=client)
    expires = datetime.now(UTC) + timedelta(minutes=5)
    upload, headers, _ = await storage.presign_upload(
        "globalchat-private",
        "organizations/org/conversations/con/media/id/original",
        "image/jpeg",
        expires,
    )
    download = await storage.presign_download(
        "globalchat-private", "organizations/org/conversations/con/media/id/original", 300
    )
    await storage.delete(
        "globalchat-private", "organizations/org/conversations/con/media/id/original"
    )
    assert upload.endswith("put_object")
    assert download.endswith("get_object")
    assert headers == {"Content-Type": "image/jpeg"}
    put = client.calls[0][1]
    get = client.calls[1][1]
    assert put["Params"] == {
        "Bucket": "globalchat-private",
        "Key": "organizations/org/conversations/con/media/id/original",
        "ContentType": "image/jpeg",
    }
    assert get["Params"] == {
        "Bucket": "globalchat-private",
        "Key": "organizations/org/conversations/con/media/id/original",
    }
    assert all("ACL" not in call[1] for call in client.calls)


@pytest.mark.asyncio
async def test_s3_failure_is_sanitized_and_readiness_checks_private_bucket():
    class FailingClient(S3Client):
        def head_object(self, **kwargs):
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "HeadObject")

        def head_bucket(self, **kwargs):
            raise ClientError({"Error": {"Code": "AccessDenied"}}, "HeadBucket")

    storage = S3PrivateStorage(
        region="ap-south-1", bucket="globalchat-private", client=FailingClient()
    )
    with pytest.raises(StorageError, match="storage request failed"):
        await storage.head("globalchat-private", "organizations/org/media/id/original")
    assert not await storage.ready()


@pytest.mark.asyncio
async def test_media_service_generates_tenant_safe_keys_and_rejects_cross_tenant_access():
    org, conversation = uuid4(), uuid4()
    owner = Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    service = MediaService(
        S3PrivateStorage(region="ap-south-1", bucket="private", client=S3Client())
    )
    result = await service.initiate(
        owner,
        UploadRequest(
            conversation_id=conversation,
            filename="../../secret.jpg",
            mime_type="image/jpeg",
            size_bytes=7,
            media_type="image",
        ),
    )
    media = service.media[result["media_id"]]
    assert media.object_key.startswith(f"organizations/{org}/conversations/{conversation}/media/")
    assert ".." not in media.object_key
    intruder = Principal(uuid4(), uuid4(), uuid4(), uuid4(), frozenset({conversation}))
    with pytest.raises(Exception, match="media not found"):
        await service.download(intruder, media.id)


def test_health_routes_are_unauthenticated_and_report_storage_readiness():
    with TestClient(app) as client:
        assert client.get("/health/live").json() == {"status": "alive"}
        assert client.get("/health/ready").json() == {"status": "ready", "storage": "available"}
        app.state.media_service.storage.fail = True
        assert client.get("/health/ready").status_code == 503
