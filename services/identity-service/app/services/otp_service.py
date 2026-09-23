import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import DomainError
from app.models.models import OTPChallenge, OTPStatus
from app.security.hashing import hash_secret, verify_secret
from app.security.phone import normalize_phone
from app.services.audit import audit_and_event
from app.services.rate_limit import RateLimiter


class OTPProvider:
    async def send_otp(self, phone: str, code: str) -> None:
        raise NotImplementedError


class DevelopmentOTPProvider(OTPProvider):
    async def send_otp(self, phone: str, code: str) -> None:
        return None  # returned only from explicitly enabled local API behavior


class OTPService:
    def __init__(self, provider: OTPProvider, limiter: RateLimiter):
        self.provider = provider
        self.limiter = limiter

    async def request(
        self, db: AsyncSession, phone_input: str, purpose: str, ip: str, correlation_id: str
    ) -> tuple[OTPChallenge, str | None]:
        settings = get_settings()
        phone = normalize_phone(phone_input)
        await self.limiter.hit(f"otp:ip:{ip}", 10, 3600)
        await self.limiter.hit(f"otp:phone:{phone}", 5, 3600)
        await self.limiter.cooldown(
            f"otp:cooldown:{phone}:{purpose}", settings.otp_resend_cooldown_seconds
        )
        code = f"{secrets.randbelow(1_000_000):06d}"
        challenge = OTPChallenge(
            purpose=purpose,
            phone_number=phone,
            code_hash=hash_secret(code),
            max_attempts=settings.otp_max_attempts,
            expires_at=datetime.now(UTC) + timedelta(seconds=settings.otp_ttl_seconds),
            requested_ip=ip,
        )
        db.add(challenge)
        await db.flush()
        await audit_and_event(
            db,
            action="OTP_REQUESTED",
            event_type="auth.otp_requested.v1",
            aggregate_type="otp_challenge",
            aggregate_id=challenge.id,
            correlation_id=correlation_id,
            ip_address=ip,
        )
        await self.provider.send_otp(phone, code)
        return challenge, code if settings.development_otp_enabled else None

    async def verify(
        self, db: AsyncSession, challenge_id, code: str, ip: str, correlation_id: str
    ) -> OTPChallenge:
        await self.limiter.hit(f"otp:verify-ip:{ip}", 30, 3600)
        challenge = (
            await db.execute(
                select(OTPChallenge).where(OTPChallenge.id == challenge_id).with_for_update()
            )
        ).scalar_one_or_none()
        if challenge is None:
            raise DomainError("OTP_INVALID", "The verification code is invalid.", 400)
        now = datetime.now(UTC)
        if challenge.status == OTPStatus.VERIFIED:
            raise DomainError("OTP_REPLAYED", "The verification code has already been used.", 409)
        if (
            challenge.status == OTPStatus.LOCKED
            or challenge.attempt_count >= challenge.max_attempts
        ):
            challenge.status = OTPStatus.LOCKED
            raise DomainError("OTP_TOO_MANY_ATTEMPTS", "The verification challenge is locked.", 429)
        if challenge.expires_at <= now:
            challenge.status = OTPStatus.EXPIRED
            raise DomainError("OTP_EXPIRED", "The verification code has expired.", 400)
        if not verify_secret(code, challenge.code_hash):
            challenge.attempt_count += 1
            if challenge.attempt_count >= challenge.max_attempts:
                challenge.status = OTPStatus.LOCKED
            await audit_and_event(
                db,
                action="OTP_FAILED",
                event_type="auth.login_failed.v1",
                aggregate_type="otp_challenge",
                aggregate_id=challenge.id,
                correlation_id=correlation_id,
                ip_address=ip,
            )
            raise DomainError("OTP_INVALID", "The verification code is invalid.", 400)
        challenge.status = OTPStatus.VERIFIED
        challenge.verified_at = now
        await audit_and_event(
            db,
            action="OTP_VERIFIED",
            event_type="auth.otp_verified.v1",
            aggregate_type="otp_challenge",
            aggregate_id=challenge.id,
            correlation_id=correlation_id,
            ip_address=ip,
        )
        return challenge
