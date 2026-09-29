from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.models.models import QRStatus
from app.services.qr_service import QRService


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
async def test_expired_qr_challenge_is_rejected_before_authorization():
    challenge = SimpleNamespace(
        public_challenge_id=uuid4(),
        status=QRStatus.PENDING,
        expires_at=datetime.now(UTC) - timedelta(seconds=1),
    )

    with pytest.raises(DomainError, match="QR_CHALLENGE_EXPIRED"):
        await QRService(None).authorize(
            Db(challenge), challenge.public_challenge_id, "secret", None, "c", "ip"
        )

    assert challenge.status == QRStatus.EXPIRED
