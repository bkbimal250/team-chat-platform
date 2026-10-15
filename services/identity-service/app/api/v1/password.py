"""Email credentials converge on the existing Identity device/session system."""

import hashlib
import re
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import client_ip, context
from app.api.v1.registration import RegistrationStart, provision_registration
from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import (
    CompanyRegistration,
    EmailVerificationChallenge,
    Identity,
    IdentityStatus,
    InvitationOnboarding,
    PasswordResetChallenge,
    PersonalRegistration,
    PlatformGrant,
    Session,
    SessionStatus,
)
from app.schemas.api import DeviceInput, TokenResponse
from app.security.hashing import hash_secret, opaque_token, token_hash, verify_secret
from app.services.audit import audit_and_event
from app.services.login_context import resolve_workspace_session_context
from app.services.rate_limit import RateLimiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["email authentication"])
# Equal-cost verification for unknown addresses and OTP-only identities.
DUMMY_HASH = hash_secret("non-account dummy password")
# This is a non-tenant context used only for sessions backed by a persistent
# platform grant. It is deliberately not an organization or membership record.
PLATFORM_SESSION_CONTEXT = UUID("00000000-0000-0000-0000-000000000001")


def canonical_email(value: str) -> str:
    local_value = value.strip().lower()
    try:
        return validate_email(
            local_value, check_deliverability=False, test_environment=True
        ).normalized.lower()
    except EmailNotValidError:
        # `.local` is reserved and therefore rejected by email-validator. It is
        # accepted only for local development accounts, never for production.
        if get_settings().app_env == "development" and re.fullmatch(
            r"[^@\s]{1,64}@[A-Za-z0-9](?:[A-Za-z0-9.-]{0,251}[A-Za-z0-9])?\.local", local_value
        ):
            return local_value
        raise ValueError("Provide a valid email address.") from None


class PasswordLogin(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128, repr=False)
    device: DeviceInput
    organization_id: UUID | None = None

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return canonical_email(value)


class PasswordRegistration(RegistrationStart):
    password: str = Field(min_length=12, max_length=128, repr=False)
    device: DeviceInput

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return canonical_email(value)


class PersonalAccount(BaseModel):
    model_config = ConfigDict(extra="forbid")
    display_name: str = Field(min_length=2, max_length=200)
    email: str = Field(max_length=320)
    phone: str = Field(max_length=64)
    password: str = Field(min_length=12, max_length=128, repr=False)
    device: DeviceInput

    @field_validator("display_name")
    @classmethod
    def name(cls, value):
        return RegistrationStart.name(value)

    @field_validator("email")
    @classmethod
    def email_address(cls, value):
        return canonical_email(value)

    @field_validator("phone")
    @classmethod
    def phone_number(cls, value):
        return RegistrationStart.phone_number(value)


@router.post("/registration/personal", response_model=TokenResponse, status_code=201)
async def register_personal(
    payload: PersonalAccount, request: Request, db: AsyncSession = Depends(get_session)
):
    from app.api.v1.registration import provision

    enabled()
    await limits(request, payload.email, "register")
    try:
        async with db.begin():
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": "email:" + payload.email},
            )
            identity = await db.scalar(
                select(Identity)
                .where(func.lower(func.trim(Identity.email)) == payload.email)
                .with_for_update()
            )
            if identity:
                row = await db.get(PersonalRegistration, identity.id)
                if (
                    row is None
                    or row.completed_at is not None
                    or identity.status != IdentityStatus.PENDING
                    or row.display_name != payload.display_name
                    or identity.phone_number != payload.phone
                    or not verify_secret(payload.password, identity.password_hash or DUMMY_HASH)
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
            else:
                identity = Identity(
                    email=payload.email,
                    phone_number=payload.phone,
                    password_hash=hash_secret(payload.password),
                    status=IdentityStatus.PENDING,
                    phone_verified=False,
                    email_verified=False,
                )
                db.add(identity)
                await db.flush()
                db.add(
                    PersonalRegistration(identity_id=identity.id, display_name=payload.display_name)
                )
                await issue_email_verification(db, identity, request)
    except IntegrityError:
        raise DomainError(
            "ACCOUNT_EXISTS", "Registration is unavailable. Sign in or contact support.", 409
        ) from None
    # Persist the intent first. The internal profile provisioner is idempotent,
    # so a crash or downstream outage can safely resume the same identity.
    async with db.begin():
        row = await db.scalar(
            select(PersonalRegistration)
            .where(PersonalRegistration.identity_id == identity.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row.completed_at is not None:
            raise DomainError(
                "ACCOUNT_EXISTS", "Registration already completed. Please sign in.", 409
            )
        profile = await provision(
            "user",
            "/internal/v1/users/provision",
            {"identity_id": str(identity.id), "display_name": row.display_name},
            request.state.correlation_id,
        )
        if not isinstance(profile, dict) or profile.get("user_id") != str(identity.id):
            raise DomainError(
                "PROVISIONING_RETRY", "Profile provisioning is temporarily unavailable.", 503
            )
        identity.status = IdentityStatus.ACTIVE
        await audit_and_event(
            db,
            action="IDENTITY_CREATED",
            event_type="identity.created.v1",
            aggregate_type="identity",
            aggregate_id=identity.id,
            identity_id=identity.id,
            correlation_id=request.state.correlation_id,
            ip_address=client_ip(request),
        )
        result = await issue(db, identity, payload, None, None, request)
        row.completed_at = datetime.now(UTC)
        return result


class ForgotPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return canonical_email(value)


class PasswordReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=512, pattern=r"^[A-Za-z0-9_-]+$", repr=False)
    new_password: str = Field(min_length=12, max_length=128, repr=False)


class EmailVerification(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=512, pattern=r"^[A-Za-z0-9_-]+$", repr=False)


class EmailVerificationResend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return canonical_email(value)


GENERIC_RESET_MESSAGE = (
    "If an account exists for this email, password reset instructions have been prepared."
)
GENERIC_VERIFICATION_MESSAGE = (
    "If an eligible account exists for this email, verification instructions have been prepared."
)


def enabled():
    if not get_settings().AUTH_EMAIL_PASSWORD_ENABLED:
        raise DomainError("EMAIL_PASSWORD_DISABLED", "Email authentication is disabled.", 403)


async def limits(request, email, purpose):
    if get_settings().APP_ENV != "production":
        return
    limiter = RateLimiter(request.app.state.redis)
    await limiter.hit(
        f"password:{purpose}:ip:{client_ip(request)}", 30 if purpose == "login" else 10, 3600
    )
    digest = hashlib.sha256(email.encode()).hexdigest()
    await limiter.hit(f"password:{purpose}:email:{digest}", 20 if purpose == "login" else 10, 3600)


async def revoke_identity_sessions(db: AsyncSession, identity_id: UUID, request: Request) -> None:
    """Revoke all active sessions and their refresh families after a password reset."""
    rows = (
        await db.scalars(
            select(Session)
            .where(Session.identity_id == identity_id, Session.status == SessionStatus.ACTIVE)
            .with_for_update()
        )
    ).all()
    correlation_id, _ = context(request)
    service = SessionService()
    for session in rows:
        await service.revoke_session(
            db,
            session,
            correlation_id,
            client_ip(request),
            reason="PASSWORD_RESET_SESSION_REVOKED",
        )


async def issue_email_verification(db: AsyncSession, identity: Identity, request: Request) -> str:
    """Rotate active verification links and persist only the digest of the new token."""
    now = datetime.now(UTC)
    active = (
        await db.scalars(
            select(EmailVerificationChallenge)
            .where(
                EmailVerificationChallenge.identity_id == identity.id,
                EmailVerificationChallenge.consumed_at.is_(None),
            )
            .with_for_update()
        )
    ).all()
    for row in active:
        row.consumed_at = now
    raw_token = opaque_token()
    db.add(
        EmailVerificationChallenge(
            identity_id=identity.id,
            token_hash=token_hash(raw_token),
            requested_ip=client_ip(request),
            expires_at=now + timedelta(seconds=get_settings().EMAIL_VERIFICATION_TTL),
        )
    )
    correlation_id, user_agent = context(request)
    await audit_and_event(
        db,
        action="EMAIL_VERIFICATION_REQUESTED",
        event_type="identity.email_verification_requested.v1",
        aggregate_type="identity",
        aggregate_id=identity.id,
        identity_id=identity.id,
        correlation_id=correlation_id,
        ip_address=client_ip(request),
        user_agent=user_agent,
    )
    return raw_token


@router.post("/password/forgot")
async def forgot_password(
    payload: ForgotPassword, request: Request, db: AsyncSession = Depends(get_session)
):
    """Create a reset challenge without revealing whether the account exists."""
    enabled()
    await limits(request, payload.email, "password-reset")
    local_token: str | None = None
    async with db.begin():
        identity = await db.scalar(
            select(Identity)
            .where(func.lower(func.trim(Identity.email)) == payload.email)
            .with_for_update()
        )
        if (
            identity is not None
            and identity.status == IdentityStatus.ACTIVE
            and identity.password_hash is not None
        ):
            # A fresh request invalidates outstanding links without persisting the raw token.
            now = datetime.now(UTC)
            active = (
                await db.scalars(
                    select(PasswordResetChallenge)
                    .where(
                        PasswordResetChallenge.identity_id == identity.id,
                        PasswordResetChallenge.consumed_at.is_(None),
                    )
                    .with_for_update()
                )
            ).all()
            for row in active:
                row.consumed_at = now
            local_token = opaque_token()
            db.add(
                PasswordResetChallenge(
                    identity_id=identity.id,
                    token_hash=token_hash(local_token),
                    requested_ip=client_ip(request),
                    expires_at=now + timedelta(seconds=get_settings().PASSWORD_RESET_TTL),
                )
            )
            correlation_id, user_agent = context(request)
            await audit_and_event(
                db,
                action="PASSWORD_RESET_REQUESTED",
                event_type="identity.password_reset_requested.v1",
                aggregate_type="identity",
                aggregate_id=identity.id,
                identity_id=identity.id,
                correlation_id=correlation_id,
                ip_address=client_ip(request),
                user_agent=user_agent,
            )
    response: dict[str, str] = {"message": GENERIC_RESET_MESSAGE}
    # Local-only delivery replaces email during development. Never enable this in staging/production.
    if get_settings().app_env == "development":
        # Keep the local response shape indistinguishable for unknown/ineligible
        # emails. Only a token backed by a persisted challenge can be consumed.
        response["development_reset_token"] = local_token or opaque_token()
    return response


@router.post("/password/reset", status_code=204)
async def reset_password(
    payload: PasswordReset, request: Request, db: AsyncSession = Depends(get_session)
) -> None:
    """Consume a one-time reset token, replace the Argon2id hash, and revoke sessions."""
    enabled()
    await RateLimiter(request.app.state.redis).hit(
        f"password:reset:ip:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        row = await db.scalar(
            select(PasswordResetChallenge)
            .where(PasswordResetChallenge.token_hash == token_hash(payload.token))
            .with_for_update()
        )
        now = datetime.now(UTC)
        if row is None or row.consumed_at is not None or row.expires_at <= now:
            raise DomainError(
                "PASSWORD_RESET_INVALID", "This password reset link is invalid or expired.", 409
            )
        identity = await db.scalar(
            select(Identity).where(Identity.id == row.identity_id).with_for_update()
        )
        if identity is None or identity.status != IdentityStatus.ACTIVE:
            raise DomainError(
                "PASSWORD_RESET_INVALID", "This password reset link is invalid or expired.", 409
            )
        identity.password_hash = hash_secret(payload.new_password)
        row.consumed_at = now
        await revoke_identity_sessions(db, identity.id, request)
        correlation_id, user_agent = context(request)
        await audit_and_event(
            db,
            action="PASSWORD_RESET_COMPLETED",
            event_type="identity.password_reset_completed.v1",
            aggregate_type="identity",
            aggregate_id=identity.id,
            identity_id=identity.id,
            correlation_id=correlation_id,
            ip_address=client_ip(request),
            user_agent=user_agent,
            changed_fields=["password_hash"],
        )


@router.post("/email/verify", status_code=204)
async def verify_email(
    payload: EmailVerification, request: Request, db: AsyncSession = Depends(get_session)
) -> None:
    """Consume a short-lived verification challenge without coupling it to password reset."""
    enabled()
    await RateLimiter(request.app.state.redis).hit(
        f"email-verification:verify:ip:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        row = await db.scalar(
            select(EmailVerificationChallenge)
            .where(EmailVerificationChallenge.token_hash == token_hash(payload.token))
            .with_for_update()
        )
        now = datetime.now(UTC)
        if row is None or row.consumed_at is not None or row.expires_at <= now:
            raise DomainError(
                "EMAIL_VERIFICATION_INVALID", "This verification link is invalid or expired.", 409
            )
        identity = await db.scalar(
            select(Identity).where(Identity.id == row.identity_id).with_for_update()
        )
        if identity is None or identity.status not in {
            IdentityStatus.PENDING,
            IdentityStatus.ACTIVE,
        }:
            raise DomainError(
                "EMAIL_VERIFICATION_INVALID", "This verification link is invalid or expired.", 409
            )
        identity.email_verified = True
        identity.email_verified_at = now
        row.consumed_at = now
        correlation_id, user_agent = context(request)
        await audit_and_event(
            db,
            action="EMAIL_VERIFICATION_COMPLETED",
            event_type="identity.email_verified.v1",
            aggregate_type="identity",
            aggregate_id=identity.id,
            identity_id=identity.id,
            correlation_id=correlation_id,
            ip_address=client_ip(request),
            user_agent=user_agent,
            changed_fields=["email_verified", "email_verified_at"],
        )


@router.post("/email/verification/resend")
async def resend_email_verification(
    payload: EmailVerificationResend, request: Request, db: AsyncSession = Depends(get_session)
):
    """Prepare one fresh verification link while keeping account existence private."""
    enabled()
    await limits(request, payload.email, "email-verification")
    local_token: str | None = None
    async with db.begin():
        identity = await db.scalar(
            select(Identity)
            .where(func.lower(func.trim(Identity.email)) == payload.email)
            .with_for_update()
        )
        if (
            identity is not None
            and identity.status in {IdentityStatus.PENDING, IdentityStatus.ACTIVE}
            and identity.email_verified is False
        ):
            local_token = await issue_email_verification(db, identity, request)
    response: dict[str, str] = {"message": GENERIC_VERIFICATION_MESSAGE}
    # Local-only delivery intentionally preserves the generic response shape.
    if get_settings().app_env == "development":
        response["development_verification_token"] = local_token or opaque_token()
    return response


async def issue(db, identity, payload, organization_id, member_id, request):
    sessions = SessionService()
    device = await sessions.device(db, identity.id, payload.device)
    correlation_id, user_agent = context(request)
    return await sessions.create(
        db,
        identity=identity,
        device=device,
        organization_id=organization_id,
        member_id=member_id,
        ip=client_ip(request),
        user_agent=user_agent,
        correlation_id=correlation_id,
    )


async def platform_context(db: AsyncSession, identity_id: UUID) -> tuple[UUID, UUID] | None:
    """Return a non-tenant session context only for an active persistent grant."""
    grant = await db.get(PlatformGrant, identity_id)
    if grant and grant.active and grant.role in {"SUPER_ADMIN", "ADMIN"}:
        return PLATFORM_SESSION_CONTEXT, PLATFORM_SESSION_CONTEXT
    return None


@router.post("/login", response_model=TokenResponse)
async def login(payload: PasswordLogin, request: Request, db: AsyncSession = Depends(get_session)):
    enabled()
    await limits(request, payload.email, "login")
    async with db.begin():
        identity = await db.scalar(
            select(Identity)
            .where(func.lower(func.trim(Identity.email)) == payload.email)
            .with_for_update()
        )
        valid = verify_secret(
            payload.password,
            identity.password_hash if identity and identity.password_hash else DUMMY_HASH,
        )
        if (
            not valid
            or identity is None
            or not identity.password_hash
            or identity.status != IdentityStatus.ACTIVE
        ):
            raise DomainError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        # Platform-only accounts deliberately have no workspace membership.
        # Resolve their persistent grant before contacting Organization so an
        # administrative session remains independent from tenant availability.
        context = await platform_context(db, identity.id)
        if context is not None:
            return await issue(db, identity, payload, context[0], context[1], request)
        organization_id, member_id = await resolve_workspace_session_context(
            identity.id, payload.organization_id, request.state.correlation_id
        )
        return await issue(db, identity, payload, organization_id, member_id, request)


@router.post("/registration/company", response_model=TokenResponse, status_code=201)
async def register(
    payload: PasswordRegistration, request: Request, db: AsyncSession = Depends(get_session)
):
    enabled()
    await limits(request, payload.email, "register")
    failure = None
    try:
        async with db.begin():
            # Same canonical email serializes retries and concurrent initial requests.
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": "email:" + payload.email},
            )
            identity = await db.scalar(
                select(Identity)
                .where(func.lower(func.trim(Identity.email)) == payload.email)
                .with_for_update()
            )
            if identity:
                row = await db.scalar(
                    select(CompanyRegistration)
                    .where(CompanyRegistration.identity_id == identity.id)
                    .with_for_update()
                )
                if (
                    row is None
                    or row.challenge_id is not None
                    or row.state == "COMPLETED"
                    or not identity.password_hash
                    or not verify_secret(payload.password, identity.password_hash or DUMMY_HASH)
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
                if (row.company_name, row.owner_name, row.phone_number) != (
                    payload.company_name,
                    payload.owner_name,
                    payload.phone,
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
            else:
                if await db.scalar(
                    select(Identity.id).where(Identity.phone_number == payload.phone)
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
                identity = Identity(
                    email=payload.email,
                    phone_number=payload.phone,
                    password_hash=hash_secret(payload.password),
                    phone_verified=False,
                    email_verified=False,
                    status=IdentityStatus.PENDING,
                )
                db.add(identity)
                await db.flush()
                await issue_email_verification(db, identity, request)
                row = CompanyRegistration(
                    company_name=payload.company_name,
                    owner_name=payload.owner_name,
                    email=payload.email,
                    phone_number=payload.phone,
                    identity_id=identity.id,
                    organization_id=uuid4(),
                    state="VERIFIED",
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
                db.add(row)
                await db.flush()
    except IntegrityError:
        raise DomainError(
            "ACCOUNT_EXISTS", "Registration is unavailable. Sign in or contact support.", 409
        ) from None
    # The durable intent above survives downstream failure, retaining the same IDs.
    async with db.begin():
        row = await db.scalar(
            select(CompanyRegistration)
            .where(CompanyRegistration.identity_id == identity.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row.state == "COMPLETED":
            raise DomainError(
                "ACCOUNT_EXISTS", "Registration already completed. Please sign in.", 409
            )
        try:
            await provision_registration(db, row, request.state.correlation_id, client_ip(request))
            result = await issue(db, identity, payload, row.organization_id, row.member_id, request)
            row.state, row.last_error = "COMPLETED", None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning is temporarily unavailable.", 503
            )
    if failure:
        raise failure
    return result


class InvitationPassword(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(max_length=320)
    password: str = Field(min_length=1, max_length=128, repr=False)
    device: DeviceInput

    @field_validator("email")
    @classmethod
    def normalize(cls, value):
        return canonical_email(value)

    token: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$", repr=False)


@router.post("/invitations/password", response_model=TokenResponse)
async def invitation_password(
    payload: InvitationPassword, request: Request, db: AsyncSession = Depends(get_session)
):
    from app.api.v1.invitations import organization
    from app.api.v1.registration import provision

    enabled()
    await limits(request, payload.email, "register")
    digest = hashlib.sha256(payload.token.encode()).hexdigest()
    failure = None
    try:
        async with db.begin():
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": "email:" + payload.email},
            )
            row = await db.scalar(
                select(InvitationOnboarding)
                .where(InvitationOnboarding.token_hash == digest)
                .with_for_update()
            )
            identity = await db.scalar(
                select(Identity)
                .where(func.lower(func.trim(Identity.email)) == payload.email)
                .with_for_update()
            )
            if row:
                if (
                    row.challenge_id is not None
                    or row.state != "VERIFIED"
                    or row.expires_at <= datetime.now(UTC)
                    or identity is None
                    or row.identity_id != identity.id
                ):
                    raise DomainError(
                        "INVITATION_INVALID",
                        "Invitation cannot be accepted. Sign in or contact your administrator.",
                        409,
                    )
            else:
                data = await organization(
                    "validate", {"token": payload.token}, request.state.correlation_id
                )
                if not data.get("email") or canonical_email(data["email"]) != payload.email:
                    raise DomainError("INVITATION_INVALID", "Invitation cannot be accepted.", 403)
                if identity is None:
                    if not 12 <= len(payload.password) <= 128:
                        raise DomainError(
                            "PASSWORD_POLICY", "Use a password between 12 and 128 characters.", 422
                        )
                    # A supplied phone is not proof: retain it in invitation metadata, never
                    # merge another phone identity or mark it verified.
                    identity = Identity(
                        email=payload.email,
                        password_hash=hash_secret(payload.password),
                        status=IdentityStatus.PENDING,
                        phone_verified=False,
                        email_verified=False,
                    )
                    db.add(identity)
                    await db.flush()
                row = InvitationOnboarding(
                    invitation_id=UUID(data["invitation_id"]),
                    token_hash=digest,
                    phone_number=data.get("phone") or "",
                    recipient_name=data["recipient_name"],
                    organization_id=UUID(data["organization_id"]),
                    identity_id=identity.id,
                    state="VERIFIED",
                    expires_at=datetime.fromisoformat(data["expires_at"]),
                )
                db.add(row)
            valid = verify_secret(payload.password, identity.password_hash or DUMMY_HASH)
            if (
                not valid
                or not identity.password_hash
                or identity.status not in {IdentityStatus.ACTIVE, IdentityStatus.PENDING}
            ):
                raise DomainError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
    except IntegrityError:
        raise DomainError("INVITATION_INVALID", "Invitation cannot be accepted.", 409) from None
    async with db.begin():
        row = await db.scalar(
            select(InvitationOnboarding)
            .where(InvitationOnboarding.token_hash == digest)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row.state != "VERIFIED":
            raise DomainError(
                "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
            )
        try:
            await provision(
                "user",
                "/internal/v1/users/company-owner",
                {"identity_id": str(identity.id), "display_name": row.recipient_name},
                request.state.correlation_id,
            )
            result = await organization(
                "accept-email",
                {
                    "invitation_id": str(row.invitation_id),
                    "token_hash": digest,
                    "email": payload.email,
                    "identity_id": str(identity.id),
                },
                request.state.correlation_id,
            )
            if UUID(result["organization_id"]) != row.organization_id:
                raise DomainError(
                    "PROVISIONING_RETRY", "Onboarding is temporarily unavailable.", 503
                )
            row.member_id = UUID(result["member_id"])
            if identity.status == IdentityStatus.PENDING:
                await audit_and_event(
                    db,
                    action="IDENTITY_CREATED",
                    event_type="identity.created.v1",
                    aggregate_type="identity",
                    aggregate_id=identity.id,
                    identity_id=identity.id,
                    correlation_id=request.state.correlation_id,
                    ip_address=client_ip(request),
                )
            identity.status = IdentityStatus.ACTIVE
            if not identity.email_verified:
                await issue_email_verification(db, identity, request)
            tokens = await issue(db, identity, payload, row.organization_id, row.member_id, request)
            row.state, row.last_error = "COMPLETED", None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning is temporarily unavailable.", 503
            )
    if failure:
        raise failure
    return tokens
