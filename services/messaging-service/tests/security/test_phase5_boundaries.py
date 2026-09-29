from uuid import uuid4

import pytest

from app.core import DomainError
from app.security import Principal
from app.services import authorize


class Db:
    async def scalar(self, _):
        return None


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["send", "history", "reply", "edit", "delete", "reaction"])
async def test_cross_tenant_operations_fail_closed(operation):
    with pytest.raises(DomainError, match="Conversation access"):
        await authorize(Db(), Principal(uuid4(), uuid4(), uuid4(), uuid4()), uuid4())
