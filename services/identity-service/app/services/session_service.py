import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.models import (
    CredentialStatus,
    Device,
    DeviceStatus,
    Identity,
    RefreshCredential,
    Session,
    SessionStatus,
)
from app.schemas.api import DeviceInput, TokenResponse
from app.security.hashing import opaque_token, token_hash
from app.security.tokens import issue_access_token
from app.services.audit import audit_and_event


class SessionService:
    async def device(self, db: AsyncSession, identity_id: UUID, payload: DeviceInput) -> Device:
        device = (
            await db.execute(
                select(Device)
                .where(
                    Device.identity_id == identity_id,
                    Device.installation_id == payload.installation_id,
                )
                .with_for_update()
            )
        ).scalar_one_or_none()
        now = datetime.now(UTC)
        if device:
            if device.status != DeviceStatus.ACTIVE:
                raise DomainError("DEVICE_REVOKED", "This device cannot be used.", 403)
            (
                device.platform,
                device.device_name,
                device.device_model,
                device.os_version,
                device.app_version,
                device.last_seen_at,
            ) = (
                payload.platform,
                payload.device_name,
                payload.device_model,
                payload.os_version,
                payload.app_version,
                now,
            )
            return device
        device = Device(
            identity_id=identity_id,
            platform=payload.platform,
            device_name=payload.device_name,
            device_model=payload.device_model,
            os_version=payload.os_version,
            app_version=payload.app_version,
            installation_id=payload.installation_id,
            last_seen_at=now,
        )
        db.add(device)
        await db.flush()
        return device

    async def create(
        self,
        db: AsyncSession,
        *,
        identity: Identity,
        device: Device,
        organization_id: UUID,
        member_id: UUID,
        ip: str,
        user_agent: str,
        correlation_id: str,
        event_action: str = "LOGIN_SUCCEEDED",
    ) -> TokenResponse:
        if identity.status != "ACTIVE" or device.status != DeviceStatus.ACTIVE:
            raise DomainError("IDENTITY_INACTIVE", "Authentication is unavailable.", 403)
        settings = get_settings()
        family = uuid.uuid4()
        session = Session(
            identity_id=identity.id,
            device_id=device.id,
            organization_id=organization_id,
            member_id=member_id,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_seconds),
            refresh_family_id=family,
            ip_address=ip,
            user_agent=user_agent[:512],
        )
        db.add(session)
        await db.flush()
        raw_refresh = opaque_token()
        db.add(
            RefreshCredential(
                session_id=session.id,
                family_id=family,
                token_hash=token_hash(raw_refresh),
                expires_at=session.expires_at,
            )
        )
        identity.last_login_at = datetime.now(UTC)
        await audit_and_event(
            db,
            action="DEVICE_REGISTERED",
            event_type="device.registered.v1",
            aggregate_type="device",
            aggregate_id=device.id,
            correlation_id=correlation_id,
            identity_id=identity.id,
            organization_id=organization_id,
            member_id=member_id,
            device_id=device.id,
            ip_address=ip,
        )
        await audit_and_event(
            db,
            action="SESSION_CREATED",
            event_type="session.created.v1",
            aggregate_type="session",
            aggregate_id=session.id,
            correlation_id=correlation_id,
            identity_id=identity.id,
            organization_id=organization_id,
            member_id=member_id,
            device_id=device.id,
            session_id=session.id,
            ip_address=ip,
        )
        await audit_and_event(
            db,
            action=event_action,
            event_type="auth.login_succeeded.v1",
            aggregate_type="identity",
            aggregate_id=identity.id,
            correlation_id=correlation_id,
            identity_id=identity.id,
            organization_id=organization_id,
            member_id=member_id,
            device_id=device.id,
            session_id=session.id,
            ip_address=ip,
        )
        return TokenResponse(
            access_token=issue_access_token(
                identity_id=identity.id,
                session_id=session.id,
                device_id=device.id,
                organization_id=organization_id,
                member_id=member_id,
            ),
            expires_in=settings.access_token_ttl_seconds,
            refresh_token=raw_refresh,
            session_id=session.id,
            device_id=device.id,
            organization_id=organization_id,
            member_id=member_id,
        )

    async def refresh(
        self, db: AsyncSession, raw_token: str, ip: str, user_agent: str, correlation_id: str
    ) -> TokenResponse:
        credential = (
            await db.execute(
                select(RefreshCredential)
                .where(RefreshCredential.token_hash == token_hash(raw_token))
                .with_for_update()
            )
        ).scalar_one_or_none()
        if credential is None:
            raise DomainError("REFRESH_TOKEN_INVALID", "The refresh credential is invalid.", 401)
        session = (
            await db.execute(
                select(Session).where(Session.id == credential.session_id).with_for_update()
            )
        ).scalar_one()
        now = datetime.now(UTC)
        if credential.status != CredentialStatus.ACTIVE:
            await self.compromise_family(db, credential.family_id, correlation_id, session, ip)
            raise DomainError("REFRESH_TOKEN_REUSED", "Reauthentication is required.", 401)
        if (
            credential.expires_at <= now
            or session.expires_at <= now
            or session.status != SessionStatus.ACTIVE
        ):
            credential.status = (
                CredentialStatus.EXPIRED
                if credential.expires_at <= now
                else CredentialStatus.REVOKED
            )
            raise DomainError("SESSION_EXPIRED", "Reauthentication is required.", 401)
        identity = (
            await db.execute(select(Identity).where(Identity.id == session.identity_id))
        ).scalar_one()
        device = (
            await db.execute(select(Device).where(Device.id == session.device_id))
        ).scalar_one()
        credential.status, credential.rotated_at = CredentialStatus.ROTATED, now
        new_raw = opaque_token()
        db.add(
            RefreshCredential(
                session_id=session.id,
                family_id=credential.family_id,
                token_hash=token_hash(new_raw),
                expires_at=session.expires_at,
            )
        )
        session.last_activity_at, session.ip_address, session.user_agent = now, ip, user_agent[:512]
        settings = get_settings()
        return TokenResponse(
            access_token=issue_access_token(
                identity_id=identity.id,
                session_id=session.id,
                device_id=device.id,
                organization_id=session.organization_id,
                member_id=session.member_id,
            ),
            expires_in=settings.access_token_ttl_seconds,
            refresh_token=new_raw,
            session_id=session.id,
            device_id=device.id,
            organization_id=session.organization_id,
            member_id=session.member_id,
        )

    async def compromise_family(
        self, db: AsyncSession, family_id: UUID, correlation_id: str, source: Session, ip: str
    ) -> None:
        now = datetime.now(UTC)
        await db.execute(
            update(RefreshCredential)
            .where(RefreshCredential.family_id == family_id)
            .values(status=CredentialStatus.COMPROMISED, revoked_at=now)
        )
        await db.execute(
            update(Session)
            .where(Session.refresh_family_id == family_id, Session.status == SessionStatus.ACTIVE)
            .values(status=SessionStatus.COMPROMISED, revoked_at=now)
        )
        await audit_and_event(
            db,
            action="REFRESH_REUSED",
            event_type="security.refresh_reuse_detected.v1",
            aggregate_type="session",
            aggregate_id=source.id,
            correlation_id=correlation_id,
            identity_id=source.identity_id,
            organization_id=source.organization_id,
            member_id=source.member_id,
            device_id=source.device_id,
            session_id=source.id,
            ip_address=ip,
        )

    async def revoke_session(
        self,
        db: AsyncSession,
        session: Session,
        correlation_id: str,
        ip: str,
        reason: str = "SESSION_REVOKED",
    ) -> None:
        now = datetime.now(UTC)
        if session.status != SessionStatus.ACTIVE:
            return
        session.status, session.revoked_at = SessionStatus.REVOKED, now
        await db.execute(
            update(RefreshCredential)
            .where(
                RefreshCredential.family_id == session.refresh_family_id,
                RefreshCredential.status == CredentialStatus.ACTIVE,
            )
            .values(status=CredentialStatus.REVOKED, revoked_at=now)
        )
        await audit_and_event(
            db,
            action=reason,
            event_type="session.revoked.v1",
            aggregate_type="session",
            aggregate_id=session.id,
            correlation_id=correlation_id,
            identity_id=session.identity_id,
            organization_id=session.organization_id,
            member_id=session.member_id,
            device_id=session.device_id,
            session_id=session.id,
            ip_address=ip,
        )
