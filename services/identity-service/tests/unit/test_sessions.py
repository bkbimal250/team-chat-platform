from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core.errors import DomainError
from app.models.models import DeviceStatus
from app.schemas.api import DeviceInput
from app.services.session_service import SessionService


class Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class Db:
    async def execute(self, _):
        return Result(SimpleNamespace(status=DeviceStatus.REVOKED))


@pytest.mark.asyncio
async def test_revoked_device_cannot_be_reused():
    payload = DeviceInput(
        installation_id="installation-1234", platform="WEB", device_name="Browser"
    )
    with pytest.raises(DomainError, match="DEVICE_REVOKED"):
        await SessionService().device(Db(), uuid4(), payload)
