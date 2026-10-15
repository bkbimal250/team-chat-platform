from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.core import DomainError
from app.events import apply_projection
from app.security import Principal
from app.services import authorize


class Db:
    def __init__(self, org_member):
        self.org_member = org_member
        self.values = []

    async def scalar(self, query):
        text = str(query).lower()
        if "organization_member_projections" in text:
            return self.org_member
        if "conversation_projections" in text:
            return SimpleNamespace(status="ACTIVE", type="GROUP")
        if "conversation_member_projections" in text:
            return SimpleNamespace(status="ACTIVE", user_id=uuid4())
        return None

    async def scalars(self, _):
        return SimpleNamespace(all=lambda: [])


@pytest.mark.asyncio
async def test_inactive_org_member_denied_even_with_conversation_projection():
    org, member = uuid4(), uuid4()
    with pytest.raises(DomainError, match="Conversation access"):
        await authorize(Db(None), Principal(uuid4(), member, uuid4(), org), uuid4())


@pytest.mark.asyncio
async def test_member_removed_event_marks_org_projection():
    org, member = uuid4(), uuid4()

    class Session:
        def __init__(self):
            self.added = []

        async def scalar(self, query):
            if "processed_events" in str(query).lower():
                return None
            return None

        def add(self, row):
            self.added.append(row)

    session = Session()
    await apply_projection(
        session,
        {
            "event_id": str(uuid4()),
            "event_type": "member.removed.v2",
            "organization_id": str(org),
            "producer": "organization-service",
            "payload": {"member_id": str(member), "user_id": str(uuid4()), "status": "REMOVED"},
        },
    )
    assert any(getattr(r, "status", None) == "REMOVED" for r in session.added)


@pytest.mark.asyncio
async def test_conversation_member_left_honors_resulting_status():
    conversation_id, member_id = uuid4(), uuid4()
    row = SimpleNamespace(status="ACTIVE")

    class Session:
        def __init__(self):
            self.added = []

        async def scalar(self, query):
            if "processed_events" in str(query).lower():
                return None
            if "conversation_member_projections" in str(query).lower():
                return row
            return None

        def add(self, value):
            self.added.append(value)

    await apply_projection(
        Session(),
        {
            "event_id": str(uuid4()),
            "event_type": "conversation.member_left.v1",
            "organization_id": str(uuid4()),
            "aggregate_id": str(conversation_id),
            "producer": "conversation-service",
            "payload": {
                "conversation_id": str(conversation_id),
                "member_id": str(member_id),
                "user_id": str(uuid4()),
                "resulting_status": "LEFT",
            },
        },
    )
    assert row.status == "LEFT"
