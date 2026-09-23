import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.models import OTPChallenge, OTPStatus
from app.security.hashing import hash_text, verify_hash


class OTPRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_challenge(
        self, phone_number: str, purpose: str, ip_address: str | None = None
    ) -> OTPChallenge:
        # Generate random 6‑digit code
        code = f"{uuid.uuid4().int % 1000000:06d}"  # placeholder; real generator in service
        code_hash = hash_text(code)
        now = datetime.datetime.utcnow()
        challenge = OTPChallenge(
            id=uuid.uuid7(),
            purpose=purpose,
            phone_number=phone_number,
            code_hash=code_hash,
            status=OTPStatus.PENDING,
            attempt_count=0,
            max_attempts=settings.OTP_MAX_ATTEMPTS,
            created_at=now,
            expires_at=now + datetime.timedelta(seconds=settings.OTP_TTL),
            requested_ip=ip_address,
        )
        self.db.add(challenge)
        await self.db.flush()
        return challenge, code

    async def get_valid_challenge(self, challenge_id: uuid.UUID) -> OTPChallenge | None:
        stmt = select(OTPChallenge).where(
            OTPChallenge.id == challenge_id,
            OTPChallenge.status == OTPStatus.PENDING,
            OTPChallenge.expires_at > datetime.datetime.utcnow(),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def verify_code(self, challenge: OTPChallenge, code: str) -> bool:
        # Check attempts limit
        if challenge.attempt_count >= challenge.max_attempts:
            challenge.status = OTPStatus.LOCKED
            await self.db.flush()
            return False
        # Verify hash
        if verify_hash(code, challenge.code_hash):
            challenge.status = OTPStatus.VERIFIED
            challenge.verified_at = datetime.datetime.utcnow()
            await self.db.flush()
            return True
        else:
            challenge.attempt_count += 1
            if challenge.attempt_count >= challenge.max_attempts:
                challenge.status = OTPStatus.LOCKED
            await self.db.flush()
            return False
