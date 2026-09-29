from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import DomainError
from app.security import Principal
from app.services import authorize


class Db:
    def __init__(self, values):
        self.values = iter(values)

    async def scalar(self, _):
        return next(self.values)

    async def scalars(self, _):
        return SimpleNamespace(all=lambda: [])


@pytest.mark.asyncio
async def test_closed_conversation_denies_send():
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    conversation = SimpleNamespace(status="CLOSED", organization_id=p.organization_id, type="GROUP")
    member = SimpleNamespace(status="ACTIVE")
    with pytest.raises(DomainError):
        await authorize(Db([conversation, member]), p, uuid4())


@pytest.mark.asyncio
async def test_system_message_is_not_public_send_type():
    from app.schemas import SendMessage
    from app.services import send

    p = Principal(uuid4(), uuid4(), uuid4(), uuid4())
    conversation = SimpleNamespace(status="ACTIVE", organization_id=p.organization_id, type="GROUP")
    member = SimpleNamespace(status="ACTIVE")
    with pytest.raises(DomainError):
        await send(
            Db([conversation, member]),
            p,
            uuid4(),
            SendMessage(client_message_id=uuid4(), type="SYSTEM", text="x"),
            "c",
        )
