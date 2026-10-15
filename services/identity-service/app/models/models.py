import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    event,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


def uuid4() -> uuid.UUID:
    return uuid.uuid4()


class IdentityStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    DISABLED = "DISABLED"
    DELETED = "DELETED"


class DevicePlatform(str, enum.Enum):
    ANDROID = "ANDROID"
    IOS = "IOS"
    WEB = "WEB"


class DeviceStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    REVOKED = "REVOKED"
    BLOCKED = "BLOCKED"


class SessionStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    COMPROMISED = "COMPROMISED"


class CredentialStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    ROTATED = "ROTATED"
    REVOKED = "REVOKED"
    COMPROMISED = "COMPROMISED"
    EXPIRED = "EXPIRED"


class OTPStatus(str, enum.Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    LOCKED = "LOCKED"


class QRStatus(str, enum.Enum):
    PENDING = "PENDING"
    AUTHORIZED = "AUTHORIZED"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class OutboxStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    PUBLISHED = "PUBLISHED"
    FAILED = "FAILED"


class Timestamps:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Identity(Base, Timestamps):
    __tablename__ = "identities"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    phone_number: Mapped[str | None] = mapped_column(String(32), unique=True)
    email: Mapped[str | None] = mapped_column(String(320), unique=True)
    password_hash: Mapped[str | None] = mapped_column(String(256))
    __table_args__ = (Index("identity_canonical_email", func.lower(func.trim(email)), unique=True),)
    contact_phone_digest: Mapped[str | None] = mapped_column(String(64), unique=True, index=True)
    phone_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[IdentityStatus] = mapped_column(String(20), default=IdentityStatus.PENDING)
    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    disabled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PlatformGrant(Base, Timestamps):
    """Operator-managed platform authority, independent of tenant memberships."""

    __tablename__ = "platform_grants"
    __table_args__ = (
        CheckConstraint("role IN ('SUPER_ADMIN', 'ADMIN')", name="platform_grant_role"),
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identities.id", ondelete="RESTRICT"), primary_key=True
    )
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")


class PlatformAudit(Base):
    __tablename__ = "platform_audit"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor: Mapped[str] = mapped_column(String(200))
    action: Mapped[str] = mapped_column(String(80))
    target: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    result: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Device(Base, Timestamps):
    __tablename__ = "devices"
    __table_args__ = (
        UniqueConstraint("identity_id", "installation_id", name="device_identity_installation"),
        Index("device_identity_status", "identity_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identities.id", ondelete="RESTRICT"), index=True
    )
    platform: Mapped[DevicePlatform] = mapped_column(String(20))
    device_name: Mapped[str] = mapped_column(String(200))
    device_model: Mapped[str | None] = mapped_column(String(200))
    os_version: Mapped[str | None] = mapped_column(String(100))
    app_version: Mapped[str | None] = mapped_column(String(100))
    installation_id: Mapped[str] = mapped_column(String(256))
    status: Mapped[DeviceStatus] = mapped_column(String(20), default=DeviceStatus.ACTIVE)
    first_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class Session(Base):
    __tablename__ = "sessions"
    __table_args__ = (
        CheckConstraint(
            "(organization_id IS NULL) = (member_id IS NULL)", name="session_context_pair"
        ),
        Index("session_identity_status", "identity_id", "status"),
        Index("session_context", "organization_id", "member_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id", ondelete="RESTRICT"))
    device_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("devices.id", ondelete="RESTRICT"))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    status: Mapped[SessionStatus] = mapped_column(String(20), default=SessionStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    last_activity_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refresh_family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(String(512), default="")


class RefreshCredential(Base):
    __tablename__ = "refresh_credentials"
    __table_args__ = (Index("refresh_family_status", "family_id", "status"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("sessions.id", ondelete="RESTRICT"), index=True
    )
    family_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    token_hash: Mapped[str] = mapped_column(String(256), unique=True)
    status: Mapped[CredentialStatus] = mapped_column(String(20), default=CredentialStatus.ACTIVE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    rotated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class PasswordResetChallenge(Base):
    """One-time opaque reset challenge; only its SHA-256 digest is persisted."""

    __tablename__ = "password_reset_challenges"
    __table_args__ = (
        Index("password_reset_identity_active", "identity_id", "consumed_at", "expires_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identities.id", ondelete="RESTRICT"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    requested_ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class EmailVerificationChallenge(Base):
    """One-time opaque email-verification challenge; only its digest is persisted."""

    __tablename__ = "email_verification_challenges"
    __table_args__ = (
        Index("email_verification_identity_active", "identity_id", "consumed_at", "expires_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identities.id", ondelete="RESTRICT"), index=True
    )
    token_hash: Mapped[str] = mapped_column(String(256), unique=True, nullable=False)
    requested_ip: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class OTPChallenge(Base):
    __tablename__ = "otp_challenges"
    __table_args__ = (
        Index("otp_phone_created", "phone_number", "created_at"),
        Index("otp_provider_request", "provider_request_id"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    purpose: Mapped[str] = mapped_column(String(20))
    phone_number: Mapped[str] = mapped_column(String(32))
    code_hash: Mapped[str] = mapped_column(String(256))
    status: Mapped[OTPStatus] = mapped_column(String(20), default=OTPStatus.PENDING)
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    requested_ip: Mapped[str | None] = mapped_column(String(64))
    provider_request_id: Mapped[str | None] = mapped_column(String(128), unique=True)


class QRLoginChallenge(Base):
    __tablename__ = "qr_login_challenges"
    public_challenge_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    secret_hash: Mapped[str] = mapped_column(String(256))
    status: Mapped[QRStatus] = mapped_column(String(20), default=QRStatus.PENDING, index=True)
    requesting_installation_id: Mapped[str] = mapped_column(String(256))
    requesting_platform: Mapped[DevicePlatform] = mapped_column(String(20))
    requesting_device_name: Mapped[str] = mapped_column(String(200))
    authorized_identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    authorized_device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class MembershipProjection(Base):
    __tablename__ = "membership_projections"
    __table_args__ = (
        UniqueConstraint("organization_id", "member_id", name="membership_projection_key"),
        Index("membership_identity_active", "identity_id", "status"),
    )
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    identity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    status: Mapped[str] = mapped_column(String(20))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ProcessedEvent(Base):
    """Durable redelivery guard for Organization event consumers."""

    __tablename__ = "processed_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    producer: Mapped[str] = mapped_column(String(80), nullable=False)
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class SecurityAuditEvent(Base):
    __tablename__ = "security_audit_events"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    identity_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), index=True)
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    device_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    session_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    action: Mapped[str] = mapped_column(String(100))
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64))
    user_agent: Mapped[str] = mapped_column(String(512), default="")
    correlation_id: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OutboxEvent(Base):
    __tablename__ = "outbox_events"
    __table_args__ = (Index("outbox_status_available", "status", "available_at"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, default=uuid4)
    event_type: Mapped[str] = mapped_column(String(100))
    event_version: Mapped[int] = mapped_column(Integer, default=1)
    aggregate_type: Mapped[str] = mapped_column(String(80))
    aggregate_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    organization_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    correlation_id: Mapped[str] = mapped_column(String(128))
    payload: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[OutboxStatus] = mapped_column(String(20), default=OutboxStatus.PENDING)
    retry_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    available_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str] = mapped_column(Text, default="")


class PersonalRegistration(Base, Timestamps):
    """Durable profile provisioning intent; retries reuse the same identity."""

    __tablename__ = "personal_registrations"
    identity_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("identities.id"), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(200))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class CompanyRegistration(Base, Timestamps):
    """Durable onboarding saga; authoritative input is never taken from verification."""

    __tablename__ = "company_registrations"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    company_name: Mapped[str] = mapped_column(String(200))
    owner_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(254))
    phone_number: Mapped[str] = mapped_column(String(32))
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("otp_challenges.id"), unique=True
    )
    identity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("identities.id"), unique=True)
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(20), default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_error: Mapped[str | None] = mapped_column(String(64))
    verified_code_hash: Mapped[str | None] = mapped_column(String(256))
    resume_attempts: Mapped[int] = mapped_column(Integer, default=0)


class InvitationOnboarding(Base, Timestamps):
    """Phone-bound, service-owned acceptance intent. Never stores invitation plaintext."""

    __tablename__ = "invitation_onboardings"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    invitation_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True)
    token_hash: Mapped[str] = mapped_column(String(64))
    phone_number: Mapped[str] = mapped_column(String(32))
    recipient_name: Mapped[str] = mapped_column(String(200))
    organization_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True))
    challenge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("otp_challenges.id"), unique=True
    )
    identity_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("identities.id"))
    member_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True))
    state: Mapped[str] = mapped_column(String(20), default="PENDING")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    verified_code_hash: Mapped[str | None] = mapped_column(String(256))
    resume_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(String(64))


class DeviceE2eeBundle(Base):
    """Public Signal key material for a device (no private keys)."""

    __tablename__ = "device_e2ee_bundles"
    __table_args__ = (
        CheckConstraint(
            "registration_id BETWEEN 1 AND 16383", name="e2ee_registration_id_range"
        ),
        Index("ix_device_e2ee_identity", "identity_id"),
    )
    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), primary_key=True
    )
    identity_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("identities.id", ondelete="CASCADE")
    )
    registration_id: Mapped[int] = mapped_column(Integer)
    identity_key_public: Mapped[bytes] = mapped_column()
    key_version: Mapped[int] = mapped_column(Integer, default=1, server_default="1")
    signed_prekey_id: Mapped[int] = mapped_column(Integer)
    signed_prekey_public: Mapped[bytes] = mapped_column()
    signed_prekey_signature: Mapped[bytes] = mapped_column()
    kyber_prekey_id: Mapped[int] = mapped_column(Integer)
    kyber_prekey_public: Mapped[bytes] = mapped_column()
    kyber_prekey_signature: Mapped[bytes] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    rotated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class DeviceOneTimePreKey(Base):
    __tablename__ = "device_one_time_prekeys"
    __table_args__ = (UniqueConstraint("device_id", "prekey_id", name="device_prekey_id_unique"),)
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    device_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    prekey_id: Mapped[int] = mapped_column(Integer)
    public_key: Mapped[bytes] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


# Maintain the exact-match index on all ORM identity phone changes.


@event.listens_for(Identity, "before_insert")
@event.listens_for(Identity, "before_update")
def maintain_contact_digest(mapper, connection, target):
    from app.core.config import get_settings
    from app.security.contact_phone import phone_digest

    secret = get_settings().CONTACT_MATCHING_SECRET
    target.contact_phone_digest = (
        phone_digest(target.phone_number, secret) if target.phone_number and secret else None
    )
