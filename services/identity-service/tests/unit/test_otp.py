from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.models.models import OTPStatus
from app.security.hashing import hash_secret
from app.services.otp_service import OTPService


class Limiter:
    async def hit(self, *args):
        return None


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class Db:
    def __init__(self, challenge):
        self.challenge = challenge

    async def execute(self, _):
        return Result(self.challenge)


@pytest.mark.asyncio
async def test_otp_wrong_code_locks_challenge_at_max_attempts(monkeypatch):
    challenge = SimpleNamespace(
        id=uuid4(),
        status=OTPStatus.PENDING,
        attempt_count=0,
        max_attempts=1,
        expires_at=datetime.now(UTC) + timedelta(minutes=1),
        code_hash=hash_secret("123456"),
    )
    monkeypatch.setattr("app.services.otp_service.audit_and_event", lambda *args, **kwargs: _done())

    with pytest.raises(DomainError, match="OTP_INVALID"):
        await OTPService(None, Limiter()).verify(
            Db(challenge), challenge.id, "000000", "127.0.0.1", "c"
        )

    assert challenge.attempt_count == 1
    assert challenge.status == OTPStatus.LOCKED


async def _done():
    return None
