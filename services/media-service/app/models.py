import enum
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now():
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class MediaStatus(str, enum.Enum):
    PENDING = "PENDING"
    UPLOADING = "UPLOADING"
    UPLOADED = "UPLOADED"
    READY = "READY"
    FAILED = "FAILED"
    DELETING = "DELETING"
    DELETED = "DELETED"


class Media(Base):
    __tablename__ = "media"
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    conversation_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    uploader_user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    uploader_member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    uploader_device_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    media_type: Mapped[str] = mapped_column(String(16))
    mime_type: Mapped[str] = mapped_column(String(128))
    original_filename: Mapped[str] = mapped_column(String(512))
    safe_filename: Mapped[str] = mapped_column(String(255))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    checksum_sha256: Mapped[str | None] = mapped_column(String(64), nullable=True)
    bucket: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(1024), unique=True)
    thumbnail_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    status: Mapped[MediaStatus] = mapped_column(Enum(MediaStatus), index=True)
    upload_strategy: Mapped[str] = mapped_column(String(16), default="SIMPLE")
    multipart_upload_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    part_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    multipart_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    multipart_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(128))
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    aggregate_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    payload: Mapped[str] = mapped_column(String)
    correlation_id: Mapped[str] = mapped_column(String(128))
    event_version: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(16), default="PENDING")


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    event_id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)


class MediaReference(Base):
    __tablename__ = "media_references"
    __table_args__ = (
        UniqueConstraint("media_id", "message_id", name="uq_media_message_reference"),
    )
    id: Mapped[int] = mapped_column(primary_key=True)
    media_id: Mapped[object] = mapped_column(UUID(as_uuid=True), ForeignKey("media.id"), index=True)
    message_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    active: Mapped[bool] = mapped_column(default=True)


class OrganizationStorageUsage(Base):
    __tablename__ = "organization_storage_usage"
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True)
    stored_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    media_count: Mapped[int] = mapped_column(Integer, default=0)
    reserved_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now, onupdate=now)
