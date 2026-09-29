from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.security import HTTPAuthorizationCredentials

from app.core.errors import DomainError
from app.models.models import DeviceStatus, SessionStatus
from app.security import dependencies
from app.security.tokens import decode_access_token


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class Db:
    def __init__(self, values):
        self.values = iter(values)

    async def execute(self, _):
        return Result(next(self.values))


def test_invalid_access_token_is_rejected():
    with pytest.raises(DomainError) as error:
        decode_access_token("not-a-token")
    assert error.value.status_code == 401


@pytest.mark.asyncio
async def test_missing_organization_claim_is_rejected(monkeypatch):
    claims = {"sid": str(uuid4()), "sub": str(uuid4()), "did": str(uuid4()), "mid": str(uuid4())}
    monkeypatch.setattr(dependencies, "decode_access_token", lambda _: claims)
    request = SimpleNamespace(state=SimpleNamespace())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(DomainError, match="Authentication is required"):
        await dependencies.current_principal(request, credentials, Db([]))


@pytest.mark.asyncio
async def test_revoked_session_is_rejected(monkeypatch):
    identity_id, session_id, device_id, org_id, member_id = [uuid4() for _ in range(5)]
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {
            "sub": str(identity_id),
            "sid": str(session_id),
            "did": str(device_id),
            "org": str(org_id),
            "mid": str(member_id),
        },
    )
    session = SimpleNamespace(status=SessionStatus.REVOKED)
    request = SimpleNamespace(state=SimpleNamespace())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(DomainError, match="no longer active"):
        await dependencies.current_principal(request, credentials, Db([session]))


@pytest.mark.asyncio
async def test_revoked_device_is_rejected(monkeypatch):
    identity_id, session_id, device_id, org_id, member_id = [uuid4() for _ in range(5)]
    monkeypatch.setattr(
        dependencies,
        "decode_access_token",
        lambda _: {
            "sub": str(identity_id),
            "sid": str(session_id),
            "did": str(device_id),
            "org": str(org_id),
            "mid": str(member_id),
        },
    )
    session = SimpleNamespace(
        status=SessionStatus.ACTIVE, organization_id=org_id, member_id=member_id
    )
    device = SimpleNamespace(status=DeviceStatus.REVOKED)
    request = SimpleNamespace(state=SimpleNamespace())
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="token")

    with pytest.raises(DomainError, match="no longer active"):
        await dependencies.current_principal(request, credentials, Db([session, device]))
