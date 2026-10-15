"""Invitation OTP uses the existing provider, limits and normal session machinery."""

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import client_ip, context, otp_service
from app.api.v1.registration import provision
from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_session
from app.models.models import Identity, IdentityStatus, InvitationOnboarding, OTPChallenge
from app.schemas.api import DeviceInput, TokenResponse
from app.security.hashing import hash_secret, verify_secret
from app.services.audit import audit_and_event
from app.services.rate_limit import RateLimiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth/invitations", tags=["invitation onboarding"])


class InvitationToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=32, max_length=128, pattern=r"^[A-Za-z0-9_-]+$")


class InvitationVerify(BaseModel):
    model_config = ConfigDict(extra="forbid")
    onboarding_id: UUID
    otp: str = Field(pattern=r"^\d{6}$")
    device: DeviceInput


class InvitationView(BaseModel):
    valid: bool = True
    company_name: str
    recipient_name: str
    recipient_phone_masked: str
    expires_at: datetime


class InvitationChallenge(BaseModel):
    onboarding_id: UUID
    expires_at: datetime
    resend_after: int
    development_code: str | None = None
    verified: bool = False


async def organization(action, payload, correlation_id):
    settings = get_settings()
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(10, connect=2)) as client:
            response = await client.post(
                str(settings.organization_service_url).rstrip("/")
                + "/api/internal/v1/invitations/"
                + action
                + "/",
                json=payload,
                headers={
                    "X-Internal-Service-Token": settings.internal_service_token,
                    "X-Correlation-ID": correlation_id,
                },
            )
        data = response.json()
        if response.status_code != 200:
            code = data.get("error", {}).get("code", "INVITATION_UNAVAILABLE")
            allowed = {
                "INVITATION_INVALID",
                "INVITATION_EXPIRED",
                "INVITATION_REVOKED",
                "INVITATION_ACCEPTED",
                "INVITATION_UNAVAILABLE",
                "MEMBER_INACTIVE",
                "INACTIVE_MEMBERSHIP_TARGET",
                "INVITES_DISABLED",
                "PERMISSION_DENIED",
                "ROLE_ESCALATION_DENIED",
                "TENANT_LIMIT_REACHED",
            }
            if code in allowed:
                raise DomainError(
                    code,
                    "This invitation cannot be accepted. Contact your administrator.",
                    response.status_code,
                )
            raise DomainError(
                "PROVISIONING_RETRY",
                "Onboarding is temporarily unavailable. Retry with the same code.",
                503,
            )
        return data
    except (httpx.RequestError, ValueError):
        raise DomainError(
            "PROVISIONING_RETRY",
            "Onboarding is temporarily unavailable. Retry with the same code.",
            503,
        ) from None


async def resolve(db, token, correlation_id):
    try:
        return await organization("validate", {"token": token}, correlation_id)
    except DomainError as exc:
        if exc.code != "INVITATION_ACCEPTED":
            raise
        row = await db.scalar(
            select(InvitationOnboarding).where(
                InvitationOnboarding.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                InvitationOnboarding.state == "VERIFIED",
                InvitationOnboarding.expires_at > datetime.now(UTC),
            )
        )
        if row is None or row.identity_id is None:
            raise
        return await organization(
            "resume",
            {
                "invitation_id": str(row.invitation_id),
                "token_hash": row.token_hash,
                "phone": row.phone_number,
                "identity_id": str(row.identity_id),
            },
            correlation_id,
        )


async def intent(db, onboarding_id):
    row = await db.scalar(
        select(InvitationOnboarding)
        .where(InvitationOnboarding.id == onboarding_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if row is None:
        raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
    if row.state == "COMPLETED":
        raise DomainError(
            "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
        )
    if row.expires_at <= datetime.now(UTC):
        raise DomainError("OTP_EXPIRED", "Verification has expired. Request another code.", 410)
    return row


@router.post("/validate", response_model=InvitationView)
async def validate(
    payload: InvitationToken, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:validate:{client_ip(request)}", 60, 3600
    )
    async with db.begin():
        data = await resolve(db, payload.token, request.state.correlation_id)
    phone = data["phone"]
    return InvitationView(
        company_name=data["company_name"],
        recipient_name=data["recipient_name"],
        recipient_phone_masked=phone[:3] + "•" * max(0, len(phone) - 7) + phone[-4:],
        expires_at=data["expires_at"],
    )


@router.post("/request", response_model=InvitationChallenge, status_code=202)
@router.post("/resend", response_model=InvitationChallenge, status_code=202)
async def request_otp(
    payload: InvitationToken, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:request:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        data = await resolve(db, payload.token, request.state.correlation_id)
        invitation_id = UUID(data["invitation_id"])
        token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": invitation_id.int % (2**63 - 1)}
        )
        row = await db.scalar(
            select(InvitationOnboarding)
            .where(InvitationOnboarding.invitation_id == invitation_id)
            .with_for_update()
        )
        if row and row.state == "COMPLETED":
            raise DomainError(
                "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
            )
        if (
            row
            and row.state == "VERIFIED"
            and row.token_hash == token_hash
            and row.expires_at > datetime.now(UTC)
        ):
            return InvitationChallenge(
                onboarding_id=row.id, expires_at=row.expires_at, resend_after=0, verified=True
            )
        challenge, code = await otp_service(request).request(
            db, data["phone"], "INVITATION", client_ip(request), request.state.correlation_id
        )
        if row is None:
            row = InvitationOnboarding(
                invitation_id=invitation_id,
                organization_id=UUID(data["organization_id"]),
                phone_number=data["phone"],
                recipient_name=data["recipient_name"],
            )
            db.add(row)
        row.token_hash, row.challenge_id, row.expires_at = (
            token_hash,
            challenge.id,
            challenge.expires_at,
        )
        row.state, row.verified_code_hash, row.resume_attempts = "PENDING", None, 0
        await db.flush()
        return InvitationChallenge(
            onboarding_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )


@router.post("/verify", response_model=TokenResponse)
async def verify(
    payload: InvitationVerify, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:verify:{client_ip(request)}", 30, 3600
    )
    failure = None
    async with db.begin():
        row = await intent(db, payload.onboarding_id)
        if row.state == "PENDING":
            # Binding is stored server-side. No caller-controlled phone/tenant/role fields exist.
            challenge = await db.get(OTPChallenge, row.challenge_id)
            if (
                not challenge
                or challenge.phone_number != row.phone_number
                or challenge.purpose != "INVITATION"
            ):
                raise DomainError("INVITATION_INVALID", "Verification binding is invalid.", 400)
            try:
                await otp_service(request).verify(
                    db, row.challenge_id, payload.otp, client_ip(request), correlation_id
                )
            except DomainError as exc:
                failure = exc
            if failure is None:
                key = int.from_bytes(
                    hashlib.sha256(row.phone_number.encode()).digest()[:8], "big"
                ) % (2**63 - 1)
                await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
                identity = await db.scalar(
                    select(Identity)
                    .where(Identity.phone_number == row.phone_number)
                    .with_for_update()
                )
                reserved_invitation = identity and await db.scalar(
                    select(InvitationOnboarding.id).where(
                        InvitationOnboarding.identity_id == identity.id,
                        InvitationOnboarding.state == "VERIFIED",
                    )
                )
                if (
                    identity
                    and identity.status != IdentityStatus.ACTIVE
                    and not (
                        identity.status == IdentityStatus.PENDING
                        and (reserved_invitation or row.identity_id == identity.id)
                    )
                ):
                    failure = DomainError(
                        "ACCOUNT_UNAVAILABLE", "Contact your administrator about this account.", 403
                    )
                else:
                    if identity is None:
                        identity = Identity(
                            phone_number=row.phone_number,
                            phone_verified=True,
                            status=IdentityStatus.PENDING,
                        )
                        db.add(identity)
                        await db.flush()
                    identity.phone_verified = True
                    row.identity_id, row.state = identity.id, "VERIFIED"
                    row.verified_code_hash = hash_secret(payload.otp)
                    row.expires_at = datetime.now(UTC) + timedelta(minutes=30)
        elif row.resume_attempts >= get_settings().otp_max_attempts:
            failure = DomainError("OTP_TOO_MANY_ATTEMPTS", "Verification is locked.", 429)
        elif not verify_secret(payload.otp, row.verified_code_hash or ""):
            row.resume_attempts += 1
            failure = DomainError("OTP_INVALID", "The verification code is invalid.", 400)
    if failure:
        raise failure
    async with db.begin():
        row = await intent(db, payload.onboarding_id)
        try:
            profile = await provision(
                "user",
                "/internal/v1/users/provision",
                {"identity_id": str(row.identity_id), "display_name": row.recipient_name},
                correlation_id,
            )
            UUID(profile["user_id"])
            result = await organization(
                "accept",
                {
                    "invitation_id": str(row.invitation_id),
                    "token_hash": row.token_hash,
                    "phone": row.phone_number,
                    "identity_id": str(row.identity_id),
                },
                correlation_id,
            )
            if UUID(result["organization_id"]) != row.organization_id:
                raise ValueError()
            row.member_id = UUID(result["member_id"])
            identity = await db.scalar(
                select(Identity)
                .where(Identity.id == row.identity_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if identity.status == IdentityStatus.PENDING:
                identity.status = IdentityStatus.ACTIVE
                await audit_and_event(
                    db,
                    action="IDENTITY_CREATED",
                    event_type="identity.created.v1",
                    aggregate_type="identity",
                    aggregate_id=identity.id,
                    identity_id=identity.id,
                    correlation_id=correlation_id,
                    ip_address=client_ip(request),
                )
            elif identity.status != IdentityStatus.ACTIVE:
                raise DomainError("ACCOUNT_UNAVAILABLE", "This account is unavailable.", 403)
            sessions = SessionService()
            device = await sessions.device(db, identity.id, payload.device)
            tokens = await sessions.create(
                db,
                identity=identity,
                device=device,
                organization_id=row.organization_id,
                member_id=row.member_id,
                ip=client_ip(request),
                user_agent=user_agent,
                correlation_id=correlation_id,
            )
            row.state, row.verified_code_hash, row.last_error = "COMPLETED", None, None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY",
                "Onboarding is temporarily unavailable. Retry with the same code.",
                503,
            )
    if failure:
        raise failure
    return tokens
