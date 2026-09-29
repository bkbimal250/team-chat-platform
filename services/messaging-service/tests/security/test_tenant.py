from uuid import uuid4

import pytest

from app.core import DomainError
from app.security import Principal
from app.services import authorize


class Db:
    async def scalar(self, _):
        return None


@pytest.mark.asyncio
async def test_missing_tenant_projection_denies_access():
    with pytest.raises(DomainError):
        await authorize(Db(), Principal(uuid4(), uuid4(), uuid4(), uuid4()), uuid4())
