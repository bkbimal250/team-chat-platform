from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.models import Identity, QRLoginChallenge, QRStatus
from app.schemas.api import DeviceInput, QRCreateResponse
from app.security.hashing import hash_secret, new_secret, verify_secret
from app.services.audit import audit_and_event
from app.services.session_service import SessionService


class QRService:
    def __init__(self, sessions: SessionService):
        self.sessions = sessions

    async def create(
        self, db: AsyncSession, payload: DeviceInput, correlation_id: str, ip: str
    ) -> QRCreateResponse:
        settings = get_settings()
        secret = new_secret(32)
        challenge = QRLoginChallenge(
            secret_hash=hash_secret(secret),
            requesting_installation_id=payload.installation_id,
            requesting_platform=payload.platform,
            requesting_device_name=payload.device_name,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.qr_challenge_ttl_seconds),
        )
        db.add(challenge)
        await db.flush()
        await audit_and_event(
            db,
            action="QR_CHALLENGE_CREATED",
            event_type="auth.qr_challenge_created.v1",
            aggregate_type="qr_challenge",
            aggregate_id=challenge.public_challenge_id,
            correlation_id=correlation_id,
            ip_address=ip,
        )
        return QRCreateResponse(
            challenge_id=challenge.public_challenge_id,
            payload=f"{settings.organization_service_url}link-device?challenge={challenge.public_challenge_id}.{secret}",
            expires_at=challenge.expires_at,
        )

    async def locked(self, db: AsyncSession, challenge_id: UUID) -> QRLoginChallenge:
        challenge = (
            await db.execute(
                select(QRLoginChallenge)
                .where(QRLoginChallenge.public_challenge_id == challenge_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise DomainError(
                "QR_CHALLENGE_NOT_FOUND", "The QR login challenge is unavailable.", 404
            )
        if challenge.expires_at <= datetime.now(UTC) and challenge.status in {
            QRStatus.PENDING,
            QRStatus.AUTHORIZED,
        }:
            challenge.status = QRStatus.EXPIRED
        return challenge

    async def authorize(
        self,
        db: AsyncSession,
        challenge_id: UUID,
        secret: str,
        actor_session,
        correlation_id: str,
        ip: str,
    ) -> QRLoginChallenge:
        challenge = await self.locked(db, challenge_id)
        if challenge.status == QRStatus.EXPIRED:
            raise DomainError("QR_CHALLENGE_EXPIRED", "The QR login challenge has expired.", 400)
        if challenge.status != QRStatus.PENDING:
            raise DomainError(
                "QR_CHALLENGE_ALREADY_USED", "The QR login challenge is unavailable.", 409
            )
        if not verify_secret(secret, challenge.secret_hash):
            await audit_and_event(
                db,
                action="QR_REPLAY_REJECTED",
                event_type="auth.qr_replay_rejected.v1",
                aggregate_type="qr_challenge",
                aggregate_id=challenge.public_challenge_id,
                correlation_id=correlation_id,
                identity_id=actor_session.identity_id,
                session_id=actor_session.id,
                ip_address=ip,
            )
            raise DomainError("QR_CHALLENGE_INVALID", "The QR login challenge is invalid.", 400)
        challenge.status, challenge.authorized_at = QRStatus.AUTHORIZED, datetime.now(UTC)
        challenge.authorized_identity_id, challenge.authorized_device_id = (
            actor_session.identity_id,
            actor_session.device_id,
        )
        challenge.organization_id, challenge.member_id = (
            actor_session.organization_id,
            actor_session.member_id,
        )
        await audit_and_event(
            db,
            action="QR_AUTHORIZED",
            event_type="auth.qr_authorized.v1",
            aggregate_type="qr_challenge",
            aggregate_id=challenge.public_challenge_id,
            correlation_id=correlation_id,
            identity_id=actor_session.identity_id,
            organization_id=actor_session.organization_id,
            member_id=actor_session.member_id,
            device_id=actor_session.device_id,
            session_id=actor_session.id,
            ip_address=ip,
        )
        return challenge

    async def consume(
        self,
        db: AsyncSession,
        challenge_id: UUID,
        secret: str,
        ip: str,
        user_agent: str,
        correlation_id: str,
    ):
        challenge = await self.locked(db, challenge_id)
        if challenge.status == QRStatus.EXPIRED:
            raise DomainError("QR_CHALLENGE_EXPIRED", "The QR login challenge has expired.", 400)
        if challenge.status == QRStatus.CONSUMED:
            raise DomainError(
                "QR_CHALLENGE_ALREADY_USED", "The QR login challenge has already been used.", 409
            )
        if challenge.status != QRStatus.AUTHORIZED:
            raise DomainError(
                "QR_CHALLENGE_NOT_AUTHORIZED", "The QR login challenge is not authorized.", 409
            )
        if not verify_secret(secret, challenge.secret_hash):
            raise DomainError("QR_CHALLENGE_INVALID", "The QR login challenge is invalid.", 400)
        identity = (
            await db.execute(
                select(Identity).where(Identity.id == challenge.authorized_identity_id)
            )
        ).scalar_one()
        device = await self.sessions.device(
            db,
            identity.id,
            DeviceInput(
                installation_id=challenge.requesting_installation_id,
                platform=challenge.requesting_platform,
                device_name=challenge.requesting_device_name,
            ),
        )
        tokens = await self.sessions.create(
            db,
            identity=identity,
            device=device,
            organization_id=challenge.organization_id,
            member_id=challenge.member_id,
            ip=ip,
            user_agent=user_agent,
            correlation_id=correlation_id,
            event_action="QR_CONSUMED",
        )
        challenge.status, challenge.consumed_at = QRStatus.CONSUMED, datetime.now(UTC)
        await audit_and_event(
            db,
            action="DEVICE_LINKED",
            event_type="device.linked.v1",
            aggregate_type="device",
            aggregate_id=device.id,
            correlation_id=correlation_id,
            identity_id=identity.id,
            organization_id=challenge.organization_id,
            member_id=challenge.member_id,
            device_id=device.id,
            session_id=tokens.session_id,
            ip_address=ip,
        )
        return tokens
