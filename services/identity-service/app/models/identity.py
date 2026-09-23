import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, String, text
from sqlalchemy.dialects.postgresql import UUID

from .base import Base


class IdentityStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


class Identity(Base):
    __tablename__ = "identities"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid7)
    phone_number = Column(String, nullable=True, unique=True)
    email = Column(String, nullable=True, unique=True)
    phone_verified = Column(Boolean, nullable=False, server_default=text("false"))
    email_verified = Column(Boolean, nullable=False, server_default=text("false"))
    status = Column(Enum(IdentityStatus), nullable=False, server_default=text("'PENDING'"))
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=text("now()"))
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=text("now()"),
    )
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
