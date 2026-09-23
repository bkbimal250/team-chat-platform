import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def uid():
    return uuid.uuid4()


class CType(str, enum.Enum):
    DIRECT = "DIRECT"
    GROUP = "GROUP"


class CStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"
    CLOSED = "CLOSED"
    DELETED = "DELETED"


class MRole(str, enum.Enum):
    OWNER = "OWNER"
    ADMIN = "ADMIN"
    MEMBER = "MEMBER"


class MStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    LEFT = "LEFT"
    REMOVED = "REMOVED"


class Conversation(Base):
    __tablename__ = "conversations"
    __table_args__ = (
        UniqueConstraint("organization_id", "direct_key", name="conversation_direct_key"),
        Index("conversation_org_status", "organization_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    type: Mapped[CType] = mapped_column(String(20))
    direct_key: Mapped[str | None] = mapped_column(String(80))
    title: Mapped[str | None] = mapped_column(String(200))
    description: Mapped[str | None] = mapped_column(String(2000))
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_by_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[CStatus] = mapped_column(String(20), default=CStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ConversationMember(Base):
    __tablename__ = "conversation_members"
    __table_args__ = (
        UniqueConstraint("conversation_id", "member_id", name="conversation_member_unique"),
        Index("conversation_member_lookup", "organization_id", "member_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="RESTRICT")
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    role: Mapped[MRole] = mapped_column(String(20), default=MRole.MEMBER)
    status: Mapped[MStatus] = mapped_column(String(20), default=MStatus.ACTIVE)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    left_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    added_by_member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class MemberState(Base):
    __tablename__ = "conversation_member_states"
    __table_args__ = (
        UniqueConstraint("conversation_id", "member_id", name="conversation_member_state_unique"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    conversation_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("conversations.id"))
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False)
    is_pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    pinned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    muted_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_muted_forever: Mapped[bool] = mapped_column(Boolean, default=False)
    notification_level: Mapped[str] = mapped_column(String(20), default="ALL")
    last_opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ConversationSettings(Base):
    __tablename__ = "conversation_settings"
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("conversations.id"), primary_key=True
    )
    only_admins_can_add_members: Mapped[bool] = mapped_column(Boolean, default=True)
    only_admins_can_edit_info: Mapped[bool] = mapped_column(Boolean, default=True)
    members_can_invite: Mapped[bool] = mapped_column(Boolean, default=False)


class MemberProjection(Base):
    __tablename__ = "member_projections"
    __table_args__ = (
        UniqueConstraint("organization_id", "member_id", name="member_projection_unique"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20))
    display_name: Mapped[str | None] = mapped_column(String(200))
    avatar_media_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class BlockProjection(Base):
    __tablename__ = "block_projections"
    __table_args__ = (
        UniqueConstraint("blocker_user_id", "blocked_user_id", name="block_projection_unique"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    blocker_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    blocked_user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ProcessedEvent(Base):
    __tablename__ = "processed_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    producer: Mapped[str] = mapped_column(String(80), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    event_type: Mapped[str] = mapped_column(String(100))
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(String(20), default="PENDING")
    retry_count: Mapped[int] = mapped_column(default=0)
    last_error: Mapped[str] = mapped_column(String(500), default="")
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
