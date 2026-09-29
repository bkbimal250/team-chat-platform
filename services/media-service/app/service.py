import math
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from fastapi import HTTPException

from app.config import MediaPolicy
from app.security import Principal, can_access
from app.storage import StorageError, expiry


def timestamp():
    return datetime.now(UTC)


def safe_filename(filename: str) -> str:
    name = filename.replace("\\", "/").split("/")[-1].strip()
    name = re.sub(r"[^A-Za-z0-9._ -]", "_", name).strip(". ")
    return name[:255] or "upload"


@dataclass
class MediaRecord:
    id: UUID
    organization_id: UUID
    conversation_id: UUID
    uploader_user_id: UUID
    uploader_member_id: UUID
    uploader_device_id: UUID
    media_type: str
    mime_type: str
    original_filename: str
    safe_filename: str
    size_bytes: int
    checksum_sha256: str | None
    bucket: str
    object_key: str
    status: str = "PENDING"
    thumbnail_object_key: str | None = None
    uploaded_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=timestamp)
    reference_count: int = 0
    upload_strategy: str = "SIMPLE"
    multipart_upload_id: str | None = None
    part_size_bytes: int | None = None
    multipart_started_at: datetime | None = None
    multipart_expires_at: datetime | None = None


class MediaService:
    def __init__(self, storage, policy: MediaPolicy | None = None):
        self.storage, self.policy = storage, policy or MediaPolicy()
        self.media: dict[UUID, MediaRecord] = {}
        self.outbox: list[dict] = []
        self.processed_events: set[str] = set()
        self.references: set[tuple[UUID, str]] = set()
        self.usage: dict[UUID, dict[str, int]] = {}

    def _authorized(self, principal, conversation_id):
        if not can_access(principal, conversation_id):
            raise HTTPException(403, "conversation access denied")

    def _validate(self, media_type, mime_type, size_bytes):
        if (
            media_type not in self.policy.allowed
            or mime_type not in self.policy.allowed[media_type]
        ):
            raise HTTPException(422, "unsupported media MIME/category")
        if size_bytes > self.policy.maximum[media_type]:
            raise HTTPException(422, "media exceeds size limit")
        if size_bytes > self.policy.max_upload_size_bytes:
            raise HTTPException(422, "media exceeds maximum upload size")

    def _part_size(self, size_bytes):
        minimum = math.ceil(size_bytes / self.policy.multipart_max_parts)
        return max(self.policy.multipart_part_size_bytes, minimum)

    def _event(self, event_type, media, correlation_id=""):
        self.outbox.append(
            {
                "event_id": str(uuid4()),
                "event_type": event_type,
                "event_version": 1,
                "organization_id": str(media.organization_id),
                "aggregate_id": str(media.id),
                "correlation_id": correlation_id,
                "payload": {
                    "media_id": str(media.id),
                    "conversation_id": str(media.conversation_id),
                },
                "status": "PENDING",
            }
        )

    async def initiate(self, principal: Principal, request, correlation_id=""):
        self._authorized(principal, request.conversation_id)
        self._validate(request.media_type, request.mime_type, request.size_bytes)
        if request.size_bytes >= self.policy.multipart_threshold_bytes:
            return await self.initiate_multipart(principal, request, correlation_id)
        media_id = uuid4()
        key = (
            f"organizations/{principal.organization_id}/conversations/{request.conversation_id}/"
            f"media/{media_id}/original"
        )
        media = MediaRecord(
            media_id,
            principal.organization_id,
            request.conversation_id,
            principal.user_id,
            principal.member_id,
            principal.device_id,
            request.media_type,
            request.mime_type,
            request.filename,
            safe_filename(request.filename),
            request.size_bytes,
            request.checksum_sha256,
            self.policy.bucket,
            key,
        )
        try:
            url, headers, expires_at = await self.storage.presign_upload(
                media.bucket,
                media.object_key,
                media.mime_type,
                expiry(self.policy.upload_ttl_seconds),
            )
        except StorageError as exc:
            media.status = "FAILED"
            self.media[media.id] = media
            self._event("media.failed.v1", media, correlation_id)
            raise HTTPException(503, "upload storage unavailable") from exc
        self.media[media.id] = media
        return {
            "media_id": media.id,
            "upload_url": url,
            "required_headers": headers,
            "expires_at": expires_at,
            "object_key": media.object_key,
            "upload_strategy": "SIMPLE",
        }

    async def initiate_multipart(self, principal: Principal, request, correlation_id=""):
        self._authorized(principal, request.conversation_id)
        self._validate(request.media_type, request.mime_type, request.size_bytes)
        media_id = uuid4()
        key = (
            f"organizations/{principal.organization_id}/conversations/{request.conversation_id}/"
            f"media/{media_id}/original"
        )
        media = MediaRecord(
            media_id,
            principal.organization_id,
            request.conversation_id,
            principal.user_id,
            principal.member_id,
            principal.device_id,
            request.media_type,
            request.mime_type,
            request.filename,
            safe_filename(request.filename),
            request.size_bytes,
            request.checksum_sha256,
            self.policy.bucket,
            key,
            status="UPLOADING",
            upload_strategy="MULTIPART",
        )
        part_size = self._part_size(media.size_bytes)
        try:
            upload_id = await self.storage.create_multipart_upload(
                media.bucket, media.object_key, media.mime_type
            )
        except StorageError as exc:
            media.status = "FAILED"
            self.media[media.id] = media
            self._event("media.failed.v1", media, correlation_id)
            raise HTTPException(503, "multipart storage unavailable") from exc
        media.multipart_upload_id = upload_id
        media.part_size_bytes = part_size
        media.multipart_started_at = timestamp()
        media.multipart_expires_at = media.multipart_started_at + timedelta(
            seconds=self.policy.pending_ttl_seconds
        )
        self.media[media.id] = media
        usage = self.usage.setdefault(
            media.organization_id, {"stored_bytes": 0, "media_count": 0, "reserved_bytes": 0}
        )
        usage.setdefault("reserved_bytes", 0)
        usage["reserved_bytes"] += media.size_bytes
        return {
            "media_id": media.id,
            "upload_id": upload_id,
            "part_size": part_size,
            "part_count": math.ceil(media.size_bytes / part_size),
            "expires_at": media.multipart_expires_at,
            "upload_strategy": "MULTIPART",
        }

    async def multipart_part_urls(self, principal, media_id, part_numbers):
        media = self._owned(principal, media_id)
        if media.status != "UPLOADING" or media.upload_strategy != "MULTIPART":
            raise HTTPException(409, "multipart upload is not active")
        if len(part_numbers) > self.policy.multipart_url_batch_limit or len(
            set(part_numbers)
        ) != len(part_numbers):
            raise HTTPException(422, "invalid multipart URL batch")
        count = math.ceil(media.size_bytes / media.part_size_bytes)
        if any(
            not isinstance(number, int) or number < 1 or number > count for number in part_numbers
        ):
            raise HTTPException(422, "invalid part number")
        expires_at = expiry(self.policy.upload_ttl_seconds)
        try:
            return [
                {
                    "part_number": number,
                    "presigned_url": await self.storage.presign_upload_part(
                        media.bucket,
                        media.object_key,
                        media.multipart_upload_id,
                        number,
                        expires_at,
                    ),
                    "expires_at": expires_at,
                }
                for number in part_numbers
            ]
        except StorageError as exc:
            raise HTTPException(503, "multipart part URL unavailable") from exc

    async def multipart_status(self, principal, media_id):
        media = self._owned(principal, media_id)
        if media.upload_strategy != "MULTIPART":
            raise HTTPException(409, "not a multipart upload")
        try:
            parts = await self.storage.list_parts(
                media.bucket, media.object_key, media.multipart_upload_id
            )
        except StorageError as exc:
            raise HTTPException(503, "multipart state unavailable") from exc
        return {
            "media_id": media.id,
            "status": media.status,
            "part_size": media.part_size_bytes,
            "part_count": math.ceil(media.size_bytes / media.part_size_bytes),
            "uploaded_parts": parts,
        }

    def _mark_ready(self, media, correlation_id):
        if media.status == "READY":
            return media
        media.status, media.uploaded_at = "UPLOADED", timestamp()
        media.status = "READY"
        usage = self.usage.setdefault(media.organization_id, {"stored_bytes": 0, "media_count": 0})
        usage.setdefault("reserved_bytes", 0)
        usage["reserved_bytes"] = max(0, usage["reserved_bytes"] - media.size_bytes)
        usage["stored_bytes"] += media.size_bytes
        usage["media_count"] += 1
        self._event("media.ready.v1", media, correlation_id)
        return media

    def _owned(self, principal, media_id):
        media = self.media.get(media_id)
        if not media or media.organization_id != principal.organization_id:
            raise HTTPException(404, "media not found")
        self._authorized(principal, media.conversation_id)
        return media

    async def complete(self, principal, media_id, correlation_id=""):
        media = self._owned(principal, media_id)
        if media.status == "READY":
            return media
        if media.status not in {"PENDING", "UPLOADING", "UPLOADED"}:
            raise HTTPException(409, "invalid media state")
        try:
            object_info = await self.storage.head(media.bucket, media.object_key)
        except StorageError as exc:
            raise HTTPException(503, "storage verification unavailable") from exc
        if (
            not object_info
            or object_info.size_bytes != media.size_bytes
            or object_info.mime_type != media.mime_type
        ):
            media.status = "FAILED"
            self._event("media.failed.v1", media, correlation_id)
            raise HTTPException(409, "uploaded object verification failed")
        return self._mark_ready(media, correlation_id)

    async def complete_multipart(self, principal, media_id, parts, correlation_id=""):
        media = self._owned(principal, media_id)
        if media.status == "READY":
            return media
        if media.status != "UPLOADING" or media.upload_strategy != "MULTIPART":
            raise HTTPException(409, "multipart upload is not active")
        count = math.ceil(media.size_bytes / media.part_size_bytes)
        numbers = [part.get("part_number") for part in parts]
        if numbers != list(range(1, count + 1)) or any(not part.get("etag") for part in parts):
            raise HTTPException(422, "multipart parts are incomplete or invalid")
        try:
            await self.storage.complete_multipart_upload(
                media.bucket, media.object_key, media.multipart_upload_id, parts
            )
            object_info = await self.storage.head(media.bucket, media.object_key)
        except StorageError as exc:
            raise HTTPException(503, "multipart completion unavailable") from exc
        if not object_info or object_info.size_bytes != media.size_bytes:
            raise HTTPException(409, "final multipart object verification failed")
        return self._mark_ready(media, correlation_id)

    async def abort_multipart(self, principal, media_id, correlation_id=""):
        media = self._owned(principal, media_id)
        if media.status in {"FAILED", "DELETED"}:
            return media
        if media.upload_strategy != "MULTIPART":
            raise HTTPException(409, "not a multipart upload")
        try:
            await self.storage.abort_multipart_upload(
                media.bucket, media.object_key, media.multipart_upload_id
            )
        except StorageError as exc:
            raise HTTPException(503, "multipart abort unavailable") from exc
        media.status, media.deleted_at = "FAILED", timestamp()
        usage = self.usage.setdefault(
            media.organization_id, {"stored_bytes": 0, "media_count": 0, "reserved_bytes": 0}
        )
        usage["reserved_bytes"] = max(0, usage.get("reserved_bytes", 0) - media.size_bytes)
        self._event("media.failed.v1", media, correlation_id)
        return media

    async def download(self, principal, media_id):
        media = self._owned(principal, media_id)
        if media.status != "READY" or media.deleted_at:
            raise HTTPException(404, "media unavailable")
        try:
            return await self.storage.presign_download(
                media.bucket, media.object_key, self.policy.upload_ttl_seconds
            )
        except StorageError as exc:
            raise HTTPException(503, "download storage unavailable") from exc

    async def delete(self, principal, media_id, correlation_id=""):
        media = self._owned(principal, media_id)
        if media.status == "DELETED":
            return media
        if media.status != "READY":
            raise HTTPException(409, "invalid media state")
        media.status = "DELETING"
        try:
            await self.storage.delete(media.bucket, media.object_key)
            if media.thumbnail_object_key:
                await self.storage.delete(media.bucket, media.thumbnail_object_key)
        except StorageError as exc:
            raise HTTPException(503, "storage deletion unavailable") from exc
        media.status, media.deleted_at = "DELETED", timestamp()
        usage = self.usage.setdefault(media.organization_id, {"stored_bytes": 0, "media_count": 0})
        usage["stored_bytes"] -= media.size_bytes
        usage["media_count"] -= 1
        self._event("media.deleted.v1", media, correlation_id)
        return media

    async def consume_message_event(self, event):
        event_id = event["event_id"]
        if event_id in self.processed_events:
            return False
        payload = event["payload"]
        media_id, message_id = UUID(payload["media_id"]), payload["message_id"]
        media = self.media.get(media_id)
        if not media or str(media.organization_id) != event["organization_id"]:
            return False
        key = (media_id, message_id)
        if event["event_type"] == "message.created.v1":
            self.references.add(key)
        elif event["event_type"] == "message.deleted.v1":
            self.references.discard(key)
        else:
            return False
        media.reference_count = sum(reference[0] == media_id for reference in self.references)
        self.processed_events.add(event_id)
        return True

    async def cleanup_orphans(self, before=None):
        before = before or timestamp() - timedelta(seconds=self.policy.pending_ttl_seconds)
        cleaned = []
        for media in self.media.values():
            if (
                media.upload_strategy == "MULTIPART"
                and media.status == "UPLOADING"
                and media.created_at < before
            ):
                try:
                    await self.abort_multipart(
                        Principal(
                            media.organization_id,
                            media.uploader_user_id,
                            media.uploader_member_id,
                            media.uploader_device_id,
                            frozenset({media.conversation_id}),
                        ),
                        media.id,
                    )
                except HTTPException:
                    continue
                cleaned.append(media.id)
                continue
            if (
                media.status == "PENDING"
                and media.created_at < before
                and not media.reference_count
            ):
                try:
                    await self.storage.delete(media.bucket, media.object_key)
                except StorageError:
                    continue
                media.status, media.deleted_at = "FAILED", timestamp()
                self._event("media.failed.v1", media)
                cleaned.append(media.id)
        return cleaned


class OutboxPublisher:
    def __init__(self, service, publish):
        self.service, self.publish = service, publish

    async def publish_pending(self):
        for event in self.service.outbox:
            if event["status"] != "PENDING":
                continue
            confirmed = await self.publish(event)
            if confirmed is False:
                raise RuntimeError("publisher confirmation failed")
            event["status"] = "PUBLISHED"
