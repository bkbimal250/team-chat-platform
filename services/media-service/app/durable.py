"""PostgreSQL-backed authoritative state for production Media operations."""

import json
from uuid import UUID

from sqlalchemy import delete, select

from app.models import (
    Media,
    MediaReference,
    MediaStatus,
    OrganizationStorageUsage,
    OutboxEvent,
    ProcessedEvent,
)
from app.service import MediaRecord, MediaService


class DurableMediaService:
    def __init__(self, storage, policy, sessions):
        self.storage = storage
        self.policy = policy
        self.sessions = sessions

    async def _hydrate(self, session) -> MediaService:
        service = MediaService(self.storage, self.policy)
        rows = (await session.scalars(select(Media))).all()
        references = (
            await session.scalars(select(MediaReference).where(MediaReference.active))
        ).all()
        counts: dict[UUID, int] = {}
        for reference in references:
            service.references.add((reference.media_id, str(reference.message_id)))
            counts[reference.media_id] = counts.get(reference.media_id, 0) + 1
        for row in rows:
            service.media[row.id] = MediaRecord(
                id=row.id,
                organization_id=row.organization_id,
                conversation_id=row.conversation_id,
                uploader_user_id=row.uploader_user_id,
                uploader_member_id=row.uploader_member_id,
                uploader_device_id=row.uploader_device_id,
                media_type=row.media_type,
                mime_type=row.mime_type,
                original_filename=row.original_filename,
                safe_filename=row.safe_filename,
                size_bytes=row.size_bytes,
                checksum_sha256=row.checksum_sha256,
                bucket=row.bucket,
                object_key=row.object_key,
                status=row.status.value if hasattr(row.status, "value") else row.status,
                thumbnail_object_key=row.thumbnail_object_key,
                uploaded_at=row.uploaded_at,
                deleted_at=row.deleted_at,
                created_at=row.created_at,
                reference_count=counts.get(row.id, 0),
                upload_strategy=row.upload_strategy,
                multipart_upload_id=row.multipart_upload_id,
                part_size_bytes=row.part_size_bytes,
                multipart_started_at=row.multipart_started_at,
                multipart_expires_at=row.multipart_expires_at,
            )
        for row in (await session.scalars(select(ProcessedEvent))).all():
            service.processed_events.add(str(row.event_id))
        for row in (await session.scalars(select(OrganizationStorageUsage))).all():
            service.usage[row.organization_id] = {
                "stored_bytes": row.stored_bytes,
                "media_count": row.media_count,
                "reserved_bytes": row.reserved_bytes,
            }
        return service

    async def _persist(self, session, service: MediaService) -> None:
        for item in service.media.values():
            await session.merge(
                Media(
                    id=item.id,
                    organization_id=item.organization_id,
                    conversation_id=item.conversation_id,
                    uploader_user_id=item.uploader_user_id,
                    uploader_member_id=item.uploader_member_id,
                    uploader_device_id=item.uploader_device_id,
                    media_type=item.media_type,
                    mime_type=item.mime_type,
                    original_filename=item.original_filename,
                    safe_filename=item.safe_filename,
                    size_bytes=item.size_bytes,
                    checksum_sha256=item.checksum_sha256,
                    bucket=item.bucket,
                    object_key=item.object_key,
                    thumbnail_object_key=item.thumbnail_object_key,
                    status=MediaStatus(item.status),
                    upload_strategy=item.upload_strategy,
                    multipart_upload_id=item.multipart_upload_id,
                    part_size_bytes=item.part_size_bytes,
                    multipart_started_at=item.multipart_started_at,
                    multipart_expires_at=item.multipart_expires_at,
                    created_at=item.created_at,
                    uploaded_at=item.uploaded_at,
                    deleted_at=item.deleted_at,
                )
            )
        for event_id in service.processed_events:
            await session.merge(ProcessedEvent(event_id=UUID(event_id)))
        await session.execute(delete(MediaReference))
        for media_id, message_id in service.references:
            session.add(MediaReference(media_id=media_id, message_id=UUID(message_id), active=True))
        for organization_id, usage in service.usage.items():
            await session.merge(
                OrganizationStorageUsage(
                    organization_id=organization_id,
                    stored_bytes=usage.get("stored_bytes", 0),
                    media_count=usage.get("media_count", 0),
                    reserved_bytes=usage.get("reserved_bytes", 0),
                )
            )
        for event in service.outbox:
            session.add(
                OutboxEvent(
                    id=UUID(event["event_id"]),
                    event_type=event["event_type"],
                    organization_id=UUID(event["organization_id"]),
                    aggregate_id=UUID(event["aggregate_id"]),
                    payload=json.dumps(event["payload"]),
                    correlation_id=event["correlation_id"],
                    event_version=event["event_version"],
                    status=event["status"],
                )
            )

    async def _mutate(self, method, *args):
        async with self.sessions.begin() as session:
            service = await self._hydrate(session)
            result = await getattr(service, method)(*args)
            await self._persist(session, service)
            return result

    async def initiate(self, *args):
        return await self._mutate("initiate", *args)

    async def initiate_multipart(self, *args):
        return await self._mutate("initiate_multipart", *args)

    async def multipart_part_urls(self, *args):
        return await self._mutate("multipart_part_urls", *args)

    async def multipart_status(self, *args):
        return await self._mutate("multipart_status", *args)

    async def complete(self, *args):
        return await self._mutate("complete", *args)

    async def complete_multipart(self, *args):
        return await self._mutate("complete_multipart", *args)

    async def abort_multipart(self, *args):
        return await self._mutate("abort_multipart", *args)

    async def download(self, *args):
        return await self._mutate("download", *args)

    async def delete(self, *args):
        return await self._mutate("delete", *args)

    async def consume_message_event(self, *args):
        return await self._mutate("consume_message_event", *args)

    async def cleanup_orphans(self, *args):
        return await self._mutate("cleanup_orphans", *args)
