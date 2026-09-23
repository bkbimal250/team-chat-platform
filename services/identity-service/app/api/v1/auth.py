from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.db.session import get_session
from app.integrations.organization_service import OrganizationServiceClient
from app.models.models import Identity, IdentityStatus, Session, SessionStatus
from app.schemas.api import (
    ContextRequest,
    MeResponse,
    OTPRequest,
    OTPRequestResponse,
    OTPVerifyRequest,
    QRAuthorizeRequest,
    QRConsumeRequest,
    QRCreateRequest,
    QRCreateResponse,
    RefreshRequest,
    RevokeResponse,
    TokenResponse,
)
from app.security.dependencies import Principal, current_principal
from app.services.audit import audit_and_event
from app.services.otp_service import DevelopmentOTPProvider, OTPService
from app.services.qr_service import QRService
from app.services.rate_limit import RateLimiter
from app.services.session_service import SessionService

router = APIRouter(prefix="/auth", tags=["authentication"])


def client_ip(request: Request) -> str:
    # Only a configured reverse-proxy layer may rewrite this before the app receives traffic.
    return request.client.host if request.client else "unknown"


def context(request: Request) -> tuple[str, str]:
    return request.state.correlation_id, request.headers.get("User-Agent", "")[:512]


def otp_service(request: Request) -> OTPService:
    return OTPService(DevelopmentOTPProvider(), RateLimiter(request.app.state.redis))


@router.post("/otp/request", response_model=OTPRequestResponse, status_code=202)
async def otp_request(
    payload: OTPRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, _ = context(request)
    async with db.begin():
        challenge, development_code = await otp_service(request).request(
            db, payload.phone_number, payload.purpose, client_ip(request), correlation_id
        )
    # Returning a challenge id is not identity enumeration; response body stays otherwise generic.
    return OTPRequestResponse(challenge_id=challenge.id, development_code=development_code)


@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(
    payload: OTPVerifyRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    async with db.begin():
        challenge = await otp_service(request).verify(
            db, payload.challenge_id, payload.code, client_ip(request), correlation_id
        )
        identity = (
            await db.execute(
                select(Identity)
                .where(Identity.phone_number == challenge.phone_number)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if identity is None:
            if get_settings().registration_policy == "INVITE_ONLY":
                raise DomainError("REGISTRATION_NOT_ALLOWED", "Authentication is unavailable.", 403)
            identity = Identity(
                phone_number=challenge.phone_number,
                phone_verified=True,
                status=IdentityStatus.ACTIVE,
            )
            db.add(identity)
            await db.flush()
            await audit_and_event(
                db,
                action="IDENTITY_CREATED",
                event_type="identity.created.v1",
                aggregate_type="identity",
                aggregate_id=identity.id,
                correlation_id=correlation_id,
                identity_id=identity.id,
                ip_address=client_ip(request),
            )
        if identity.status != IdentityStatus.ACTIVE:
            raise DomainError("IDENTITY_INACTIVE", "Authentication is unavailable.", 403)
        memberships = await OrganizationServiceClient().memberships(identity.id, correlation_id)
        active = [item for item in memberships if item.status == "ACTIVE"]
        if payload.organization_id:
            active = [item for item in active if item.organization_id == payload.organization_id]
        if not active:
            raise DomainError(
                "MEMBERSHIP_INACTIVE", "No active organization membership is available.", 403
            )
        selected = active[0]
        sessions = SessionService()
        device = await sessions.device(db, identity.id, payload.device)
        return await sessions.create(
            db,
            identity=identity,
            device=device,
            organization_id=selected.organization_id,
            member_id=selected.member_id,
            ip=client_ip(request),
            user_agent=user_agent,
            correlation_id=correlation_id,
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(f"refresh:ip:{client_ip(request)}", 60, 3600)
    correlation_id, user_agent = context(request)
    async with db.begin():
        return await SessionService().refresh(
            db, payload.refresh_token, client_ip(request), user_agent, correlation_id
        )


@router.post("/logout", response_model=RevokeResponse)
async def logout(
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        await SessionService().revoke_session(
            db, principal.session, request.state.correlation_id, client_ip(request)
        )
    return RevokeResponse(status="REVOKED")


@router.post("/logout-all", response_model=RevokeResponse)
async def logout_all(
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    """Revokes all sessions, including the current session; clients must clear all credentials."""
    async with db.begin():
        rows = (
            (
                await db.execute(
                    select(Session)
                    .where(
                        Session.identity_id == principal.identity_id,
                        Session.status == SessionStatus.ACTIVE,
                    )
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        service = SessionService()
        for row in rows:
            await service.revoke_session(
                db, row, request.state.correlation_id, client_ip(request), "LOGOUT_ALL"
            )
    return RevokeResponse(status="REVOKED")


@router.post("/context", response_model=TokenResponse)
async def switch_context(
    payload: ContextRequest,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    correlation_id, user_agent = context(request)
    membership = [
        item
        for item in await OrganizationServiceClient().memberships(
            principal.identity_id, correlation_id
        )
        if item.organization_id == payload.organization_id and item.status == "ACTIVE"
    ]
    if not membership:
        raise DomainError(
            "MEMBERSHIP_INACTIVE", "The requested organization context is unavailable.", 403
        )
    identity = (
        await db.execute(select(Identity).where(Identity.id == principal.identity_id))
    ).scalar_one()
    async with db.begin():
        return await SessionService().create(
            db,
            identity=identity,
            device=principal.device,
            organization_id=membership[0].organization_id,
            member_id=membership[0].member_id,
            ip=client_ip(request),
            user_agent=user_agent,
            correlation_id=correlation_id,
        )


@router.get("/me", response_model=MeResponse)
async def me(principal: Principal = Depends(current_principal)):
    return MeResponse(
        identity={"id": principal.identity_id},
        session={"id": principal.session.id, "device_id": principal.device.id},
        context={
            "organization_id": principal.session.organization_id,
            "member_id": principal.session.member_id,
        },
    )


@router.post("/qr/challenges", response_model=QRCreateResponse, status_code=201)
async def qr_create(
    payload: QRCreateRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(f"qr:create:{payload.installation_id}", 10, 3600)
    async with db.begin():
        return await QRService(SessionService()).create(
            db, payload, request.state.correlation_id, client_ip(request)
        )


@router.get("/qr/challenges/{challenge_id}/status")
async def qr_status(challenge_id: UUID, request: Request, db: AsyncSession = Depends(get_session)):
    await RateLimiter(request.app.state.redis).hit(
        f"qr:poll:{client_ip(request)}:{challenge_id}", 60, 60
    )
    async with db.begin():
        challenge = await QRService(SessionService()).locked(db, challenge_id)
        return {
            "challenge_id": challenge.public_challenge_id,
            "status": challenge.status,
            "expires_at": challenge.expires_at,
        }


@router.post("/qr/challenges/{challenge_id}/authorize", response_model=RevokeResponse)
async def qr_authorize(
    challenge_id: UUID,
    payload: QRAuthorizeRequest,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"qr:authorize:{principal.identity_id}", 30, 3600
    )
    async with db.begin():
        await QRService(SessionService()).authorize(
            db,
            challenge_id,
            payload.secret,
            principal.session,
            request.state.correlation_id,
            client_ip(request),
        )
    return RevokeResponse(status="AUTHORIZED")


@router.post("/qr/challenges/{challenge_id}/consume", response_model=TokenResponse)
async def qr_consume(
    challenge_id: UUID,
    payload: QRConsumeRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    correlation_id, user_agent = context(request)
    async with db.begin():
        return await QRService(SessionService()).consume(
            db, challenge_id, payload.secret, client_ip(request), user_agent, correlation_id
        )
