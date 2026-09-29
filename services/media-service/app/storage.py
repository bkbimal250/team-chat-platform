"""Private object-storage adapters used by the Media Service."""

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Protocol

import boto3
from botocore.exceptions import BotoCoreError, ClientError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ObjectInfo:
    size_bytes: int
    mime_type: str


class StorageError(Exception):
    """A safe storage-boundary error suitable for application responses."""


class PrivateStorage(Protocol):
    async def presign_upload(self, bucket: str, key: str, mime_type: str, expires: datetime): ...

    async def head(self, bucket: str, key: str) -> ObjectInfo | None: ...

    async def presign_download(self, bucket: str, key: str, expires: int) -> str: ...

    async def delete(self, bucket: str, key: str) -> None: ...

    async def create_multipart_upload(self, bucket: str, key: str, mime_type: str) -> str: ...

    async def presign_upload_part(
        self, bucket: str, key: str, upload_id: str, part_number: int, expires: datetime
    ) -> str: ...

    async def list_parts(self, bucket: str, key: str, upload_id: str) -> list[dict]: ...

    async def complete_multipart_upload(
        self, bucket: str, key: str, upload_id: str, parts: list[dict]
    ) -> None: ...

    async def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None: ...

    async def ready(self) -> bool: ...


class S3PrivateStorage:
    """Private S3 adapter using the standard AWS credential provider chain.

    No static access keys are accepted here. boto3 therefore uses ECS task-role
    credentials in Fargate, or the normal SDK credential chain outside ECS.
    """

    def __init__(self, *, region: str, bucket: str, endpoint_url: str | None = None, client=None):
        self.bucket = bucket
        self.client = client or boto3.client("s3", region_name=region, endpoint_url=endpoint_url)

    @staticmethod
    def _seconds(expires: datetime | int) -> int:
        if isinstance(expires, int):
            return max(1, expires)
        return max(1, int((expires - datetime.now(UTC)).total_seconds()))

    async def _call(self, operation: str, func, *args, **kwargs):
        try:
            return await asyncio.to_thread(func, *args, **kwargs)
        except (BotoCoreError, ClientError) as exc:
            logger.warning(
                "s3_operation_failed",
                extra={"operation": operation, "error": type(exc).__name__},
            )
            raise StorageError("storage request failed") from exc

    async def presign_upload(self, bucket: str, key: str, mime_type: str, expires: datetime):
        url = await self._call(
            "presign_upload",
            self.client.generate_presigned_url,
            "put_object",
            Params={"Bucket": bucket, "Key": key, "ContentType": mime_type},
            ExpiresIn=self._seconds(expires),
            HttpMethod="PUT",
        )
        return url, {"Content-Type": mime_type}, expires

    async def head(self, bucket: str, key: str) -> ObjectInfo | None:
        try:
            response = await self._call("head", self.client.head_object, Bucket=bucket, Key=key)
        except StorageError as exc:
            cause = exc.__cause__
            error_code = (
                cause.response.get("Error", {}).get("Code")
                if isinstance(cause, ClientError)
                else None
            )
            if error_code in {"404", "NoSuchKey", "NotFound"}:
                return None
            raise
        return ObjectInfo(int(response["ContentLength"]), response.get("ContentType", ""))

    async def presign_download(self, bucket: str, key: str, expires: int) -> str:
        return await self._call(
            "presign_download",
            self.client.generate_presigned_url,
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=self._seconds(expires),
            HttpMethod="GET",
        )

    async def delete(self, bucket: str, key: str) -> None:
        await self._call("delete", self.client.delete_object, Bucket=bucket, Key=key)

    async def create_multipart_upload(self, bucket: str, key: str, mime_type: str) -> str:
        response = await self._call(
            "create_multipart_upload",
            self.client.create_multipart_upload,
            Bucket=bucket,
            Key=key,
            ContentType=mime_type,
        )
        return response["UploadId"]

    async def presign_upload_part(
        self, bucket: str, key: str, upload_id: str, part_number: int, expires: datetime
    ) -> str:
        return await self._call(
            "presign_upload_part",
            self.client.generate_presigned_url,
            "upload_part",
            Params={
                "Bucket": bucket,
                "Key": key,
                "UploadId": upload_id,
                "PartNumber": part_number,
            },
            ExpiresIn=self._seconds(expires),
            HttpMethod="PUT",
        )

    async def list_parts(self, bucket: str, key: str, upload_id: str) -> list[dict]:
        response = await self._call(
            "list_parts", self.client.list_parts, Bucket=bucket, Key=key, UploadId=upload_id
        )
        return [
            {"part_number": item["PartNumber"], "etag": item["ETag"], "size": item["Size"]}
            for item in response.get("Parts", [])
        ]

    async def complete_multipart_upload(
        self, bucket: str, key: str, upload_id: str, parts: list[dict]
    ) -> None:
        await self._call(
            "complete_multipart_upload",
            self.client.complete_multipart_upload,
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={
                "Parts": [
                    {"PartNumber": part["part_number"], "ETag": part["etag"]} for part in parts
                ]
            },
        )

    async def abort_multipart_upload(self, bucket: str, key: str, upload_id: str) -> None:
        await self._call(
            "abort_multipart_upload",
            self.client.abort_multipart_upload,
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
        )

    async def ready(self) -> bool:
        try:
            await self._call("head_bucket", self.client.head_bucket, Bucket=self.bucket)
        except StorageError:
            return False
        return True


class FakePrivateStorage:
    """In-memory private storage for development and isolated tests only."""

    def __init__(self):
        self.objects: dict[tuple[str, str], ObjectInfo] = {}
        self.deleted: list[tuple[str, str]] = []
        self.fail = False
        self.multipart: dict[str, dict] = {}

    async def presign_upload(self, bucket, key, mime_type, expires):
        if self.fail:
            raise StorageError("presign failed")
        return (
            f"https://private.invalid/upload/{bucket}/{key}",
            {"Content-Type": mime_type},
            expires,
        )

    async def head(self, bucket, key):
        if self.fail:
            raise StorageError("head failed")
        return self.objects.get((bucket, key))

    async def presign_download(self, bucket, key, expires):
        if self.fail:
            raise StorageError("download presign failed")
        return f"https://private.invalid/download/{bucket}/{key}?expires={expires}"

    async def delete(self, bucket, key):
        if self.fail:
            raise StorageError("delete failed")
        self.deleted.append((bucket, key))
        self.objects.pop((bucket, key), None)

    async def create_multipart_upload(self, bucket, key, mime_type):
        if self.fail:
            raise StorageError("multipart initiation failed")
        upload_id = f"upload-{len(self.multipart) + 1}"
        self.multipart[upload_id] = {
            "bucket": bucket,
            "key": key,
            "mime_type": mime_type,
            "parts": {},
        }
        return upload_id

    async def presign_upload_part(self, bucket, key, upload_id, part_number, expires):
        if self.fail or upload_id not in self.multipart:
            raise StorageError("part presign failed")
        return f"https://private.invalid/part/{upload_id}/{part_number}?expires={expires}"

    async def list_parts(self, bucket, key, upload_id):
        if self.fail or upload_id not in self.multipart:
            raise StorageError("list parts failed")
        return [
            {"part_number": number, "etag": value["etag"], "size": value["size"]}
            for number, value in sorted(self.multipart[upload_id]["parts"].items())
        ]

    async def complete_multipart_upload(self, bucket, key, upload_id, parts):
        if self.fail or upload_id not in self.multipart:
            raise StorageError("multipart completion failed")
        upload = self.multipart[upload_id]
        expected = upload["parts"]
        if [(part["part_number"], part["etag"]) for part in parts] != [
            (number, value["etag"]) for number, value in sorted(expected.items())
        ]:
            raise StorageError("parts do not match S3 upload")
        self.objects[(bucket, key)] = ObjectInfo(
            sum(value["size"] for value in expected.values()), upload["mime_type"]
        )

    async def abort_multipart_upload(self, bucket, key, upload_id):
        if self.fail:
            raise StorageError("multipart abort failed")
        self.multipart.pop(upload_id, None)

    async def ready(self) -> bool:
        return not self.fail

    def add_part(self, upload_id, part_number, etag, size):
        self.multipart[upload_id]["parts"][part_number] = {"etag": etag, "size": size}


def expiry(seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)
