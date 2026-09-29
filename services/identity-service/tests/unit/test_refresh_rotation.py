from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.models.models import CredentialStatus, SessionStatus
from app.services.session_service import SessionService


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value

    def scalar_one(self):
        return self.value


class Db:
    def __init__(self, credential, session):
        self.values = [credential, session]

    async def execute(self, _):
        return Result(self.values.pop(0))


@pytest.mark.asyncio
async def test_reused_refresh_token_compromises_its_family(monkeypatch):
    credential = SimpleNamespace(
        status=CredentialStatus.ROTATED, family_id=uuid4(), session_id=uuid4()
    )
    session = SimpleNamespace(id=uuid4(), status=SessionStatus.ACTIVE)
    called = []

    async def compromise(*args):
        called.append(args[1])

    service = SessionService()
    monkeypatch.setattr(service, "compromise_family", compromise)
    with pytest.raises(DomainError, match="REFRESH_TOKEN_REUSED"):
        await service.refresh(Db(credential, session), "reused", "ip", "agent", "c")
    assert called == [credential.family_id]
