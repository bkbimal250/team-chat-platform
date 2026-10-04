"""Verified company-owner onboarding: durable, retryable service-owned saga."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import httpx
from email_validator import EmailNotValidError, validate_email
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import client_ip, context, otp_service
from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import CompanyRegistration, Identity, IdentityStatus
from app.schemas.api import DeviceInput, TokenResponse
from app.security.hashing import hash_secret, verify_secret
from app.security.phone import normalize_phone
from app.services.audit import audit_and_event
from app.services.rate_limit import RateLimiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth/registration/company", tags=["company registration"])


class RegistrationStart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    company_name: str = Field(min_length=2, max_length=200)
    owner_name: str = Field(min_length=2, max_length=200)
    email: str = Field(max_length=254)
    phone: str = Field(max_length=64)

    @field_validator("company_name", "owner_name")
    @classmethod
    def name(cls, value):
        value = " ".join(value.split())
        if len(value) < 2 or not any(c.isalnum() for c in value) or any(ord(c) < 32 for c in value):
            raise ValueError("Provide a valid name.")
        return value

    @field_validator("email")
    @classmethod
    def email_address(cls, value):
        value = value.strip().lower()
        try:
            validate_email(value, check_deliverability=False, test_environment=True)
        except EmailNotValidError:
            raise ValueError("Provide a valid email address.") from None
        return value

    @field_validator("phone")
    @classmethod
    def phone_number(cls, value):
        return normalize_phone(value)


class RegistrationVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registration_id: UUID
    otp: str = Field(pattern=r"^\d{6}$")
    device: DeviceInput


class RegistrationResend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    registration_id: UUID


class RegistrationChallenge(BaseModel):
    registration_id: UUID
    expires_at: datetime
    resend_after: int
    development_code: str | None = None


async def registration(db, registration_id):
    row = await db.scalar(
        select(CompanyRegistration)
        .where(CompanyRegistration.id == registration_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise DomainError("REGISTRATION_INVALID", "Registration is unavailable.", 404)
    if row.state == "COMPLETED":
        raise DomainError(
            "REGISTRATION_COMPLETED", "Company already registered. Please sign in.", 409
        )
    if row.expires_at <= datetime.now(UTC):
        raise DomainError(
            "REGISTRATION_EXPIRED",
            "Registration has expired. Contact support if provisioning had started.",
            410,
        )
    return row


@router.post("/start", response_model=RegistrationChallenge, status_code=202)
async def start(
    payload: RegistrationStart, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"registration:start:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        # Stable contact lock serializes simultaneous start submissions before any row exists.
        key = int.from_bytes(hashlib.sha256(payload.phone.encode()).digest()[:8], "big") % (
            2**63 - 1
        )
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        existing = await db.scalar(
            select(Identity.id).where(
                or_(
                    Identity.phone_number == payload.phone,
                    func.lower(Identity.email) == payload.email,
                )
            )
        )
        if existing:
            raise DomainError(
                "ACCOUNT_EXISTS", "An account already exists. Sign in or contact support.", 409
            )
        # Same contact/name submission resumes the pending record, never creates another saga.
        pending = await db.scalar(
            select(CompanyRegistration)
            .where(
                CompanyRegistration.phone_number == payload.phone,
                CompanyRegistration.expires_at > datetime.now(UTC),
                CompanyRegistration.state == "PENDING",
            )
            .with_for_update()
        )
        if pending:
            raise DomainError(
                "REGISTRATION_PENDING",
                "Registration already started. Continue verification or wait for expiry.",
                409,
            )
        challenge, code = await otp_service(request).request(
            db, payload.phone, "REGISTER", client_ip(request), request.state.correlation_id
        )
        row = CompanyRegistration(
            company_name=payload.company_name,
            owner_name=payload.owner_name,
            email=payload.email,
            phone_number=payload.phone,
            challenge_id=challenge.id,
            organization_id=uuid4(),
            expires_at=challenge.expires_at,
        )
        db.add(row)
        await db.flush()
        return RegistrationChallenge(
            registration_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )


@router.post("/resend", response_model=RegistrationChallenge, status_code=202)
async def resend(
    payload: RegistrationResend, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"registration:resend:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        row = await registration(db, payload.registration_id)
        if row.state != "PENDING":
            raise DomainError(
                "REGISTRATION_VERIFIED",
                "Resume provisioning instead of requesting another code.",
                409,
            )
        challenge, code = await otp_service(request).request(
            db, row.phone_number, "REGISTER", client_ip(request), request.state.correlation_id
        )
        row.challenge_id, row.expires_at = challenge.id, challenge.expires_at
        return RegistrationChallenge(
            registration_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )


async def provision(service: str, route: str, payload: dict, correlation_id: str) -> dict:
    settings = get_settings()
    base = str(
        settings.organization_service_url
        if service == "organization"
        else settings.USER_SERVICE_URL
    ).rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=2)) as client:
            response = await client.post(
                base + route,
                json=payload,
                headers={
                    "X-Internal-Service-Token": settings.internal_service_token,
                    "X-Correlation-ID": correlation_id,
                },
            )
        if response.status_code != 200:
            raise DomainError(
                "PROVISIONING_RETRY",
                "Provisioning could not complete. Retry verification with the same code.",
                503,
            )
        return response.json()
    except (httpx.RequestError, ValueError) as exc:
        raise DomainError(
            "PROVISIONING_RETRY",
            "Provisioning is temporarily unavailable. Retry verification with the same code.",
            503,
        ) from exc


@router.post("/verify", response_model=TokenResponse)
async def verify(
    payload: RegistrationVerify, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    limiter = RateLimiter(request.app.state.redis)
    await limiter.hit(f"registration:verify:{client_ip(request)}", 30, 3600)
    # Commit OTP failures as well, preserving attempt counters and locks.
    failure = None
    try:
        async with db.begin():
            row = await registration(db, payload.registration_id)
            if row.state == "PENDING":
                try:
                    await otp_service(request).verify(
                        db, row.challenge_id, payload.otp, client_ip(request), correlation_id
                    )
                except DomainError as exc:
                    failure = exc
                if failure is None:
                    identity = Identity(
                        phone_number=row.phone_number,
                        email=row.email,
                        phone_verified=True,
                        email_verified=False,
                        status=IdentityStatus.PENDING,
                    )
                    db.add(identity)
                    await (
                        db.flush()
                    )  # Database uniqueness serializes different challenges for one contact.
                    row.identity_id = identity.id
                    row.state = "VERIFIED"
                    row.verified_code_hash = hash_secret(payload.otp)
                    row.expires_at = datetime.now(UTC) + timedelta(minutes=30)
            else:
                if row.resume_attempts >= get_settings().otp_max_attempts:
                    failure = DomainError(
                        "OTP_TOO_MANY_ATTEMPTS", "The verification challenge is locked.", 429
                    )
                elif not verify_secret(payload.otp, row.verified_code_hash or ""):
                    row.resume_attempts += 1
                    failure = DomainError("OTP_INVALID", "The verification code is invalid.", 400)
    except IntegrityError:
        raise DomainError(
            "ACCOUNT_EXISTS", "An account already exists. Sign in or contact support.", 409
        ) from None
    if failure:
        raise failure
    # Cross-service calls are idempotent. Durable VERIFIED intent survives failures/crashes.
    async with db.begin():
        row = await registration(db, payload.registration_id)
        try:
            await provision_registration(db, row, correlation_id, client_ip(request))
        except DomainError as exc:
            row.last_error = exc.code
            failure = exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning temporarily unavailable.", 503
            )
        if failure is None:
            identity = await db.get(Identity, row.identity_id)
            sessions = SessionService()
            device = await sessions.device(db, identity.id, payload.device)
            result = await sessions.create(
                db,
                identity=identity,
                device=device,
                organization_id=row.organization_id,
                member_id=row.member_id,
                ip=client_ip(request),
                user_agent=user_agent,
                correlation_id=correlation_id,
            )
            row.state, row.last_error, row.verified_code_hash = "COMPLETED", None, None
    if failure:
        raise failure
    return result


async def provision_registration(db, row, correlation_id, ip):
    """Idempotent service-owned saga steps; caller holds the registration row lock."""
    profile = await provision(
        "user",
        "/internal/v1/users/company-owner",
        {"identity_id": str(row.identity_id), "display_name": row.owner_name},
        correlation_id,
    )
    UUID(profile["user_id"])
    company = await provision(
        "organization",
        "/api/internal/v1/company-registration/",
        {
            "organization_id": str(row.organization_id),
            "identity_id": str(row.identity_id),
            "company_name": row.company_name,
            "owner_name": row.owner_name,
            "email": row.email,
        },
        correlation_id,
    )
    if UUID(company["organization_id"]) != row.organization_id:
        raise DomainError("PROVISIONING_RETRY", "Provisioning contract mismatch.", 503)
    row.member_id = UUID(company["member_id"])
    identity = await db.get(Identity, row.identity_id)
    identity.status = IdentityStatus.ACTIVE
    await audit_and_event(
        db,
        action="IDENTITY_CREATED",
        event_type="identity.created.v1",
        aggregate_type="identity",
        aggregate_id=identity.id,
        identity_id=identity.id,
        correlation_id=correlation_id,
        ip_address=ip,
    )
