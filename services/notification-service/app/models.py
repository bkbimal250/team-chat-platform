from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, Boolean, DateTime, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class DevicePushToken(Base):
    __tablename__ = "device_push_tokens"
    __table_args__ = (UniqueConstraint("organization_id", "device_id", name="uq_push_device"),)
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    device_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    platform: Mapped[str] = mapped_column(String(16))
    provider: Mapped[str] = mapped_column(String(16))
    token: Mapped[str] = mapped_column(String(512))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)


class NotificationPreference(Base):
    __tablename__ = "notification_preferences"
    __table_args__ = (
        UniqueConstraint("organization_id", "member_id", name="uq_notification_preferences_tenant"),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    push_enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    preview: Mapped[str] = mapped_column(String(16), default="FULL", server_default="FULL")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Notification(Base):
    __tablename__ = "notifications"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "message_id",
            "recipient_member_id",
            "notification_type",
            name="uq_notification_message_recipient",
        ),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    conversation_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    message_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    recipient_user_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    recipient_member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    notification_type: Mapped[str] = mapped_column(String(32))
    title: Mapped[str | None] = mapped_column(String(255))
    body: Mapped[str | None] = mapped_column(Text)
    preview_mode: Mapped[str] = mapped_column(String(16))


class NotificationDelivery(Base):
    __tablename__ = "notification_deliveries"
    __table_args__ = (
        UniqueConstraint(
            "notification_id", "device_push_token_id", name="uq_delivery_notification_token"
        ),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    notification_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(16))
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    device_push_token_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    device_id: Mapped[object] = mapped_column(UUID(as_uuid=True), index=True)
    provider: Mapped[str] = mapped_column(String(16))
    next_attempt_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(512))
    claimed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[object] = mapped_column(UUID(as_uuid=True), unique=True)
    event_type: Mapped[str] = mapped_column(String(128))
    organization_id: Mapped[object | None] = mapped_column(UUID(as_uuid=True))


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    event_type: Mapped[str] = mapped_column(String(128))
    status: Mapped[str] = mapped_column(String(16), default="PENDING")
    event_id: Mapped[object] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid4)
    payload: Mapped[dict] = mapped_column(JSON)


class UserProjection(Base):
    __tablename__ = "user_projections"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_user_projections_tenant"),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    display_name: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(16))


class GlobalUserProjection(Base):
    """Durable global identity state emitted by User Service events."""

    __tablename__ = "global_user_projections"
    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MembershipProjection(Base):
    __tablename__ = "membership_projections"
    __table_args__ = (
        UniqueConstraint("organization_id", "member_id", name="uq_membership_projections_tenant"),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16))


class ConversationProjection(Base):
    __tablename__ = "conversation_projections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "conversation_id", name="uq_conversation_projections_tenant"
        ),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    conversation_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    conversation_type: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16))


class ConversationMemberProjection(Base):
    __tablename__ = "conversation_member_projections"
    __table_args__ = (
        UniqueConstraint(
            "organization_id",
            "conversation_id",
            "member_id",
            name="uq_conversation_member_projections_tenant",
        ),
    )
    id: Mapped[object] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    conversation_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[object] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(16))
