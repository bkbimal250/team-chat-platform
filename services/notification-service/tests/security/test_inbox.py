from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.main import list_notifications


@pytest.mark.asyncio
async def test_inbox_scopes_tenant_user_and_member_and_excludes_credentials():
    principal = SimpleNamespace(organization_id=uuid4(), member_id=uuid4(), user_id=uuid4())
    row = SimpleNamespace(
        id=uuid4(),
        conversation_id=uuid4(),
        message_id=uuid4(),
        title="Title",
        body="Body",
        preview_mode="FULL",
    )

    class Session:
        async def scalars(self, query):
            params = query.compile().params
            assert principal.organization_id in params.values()
            assert principal.member_id in params.values()
            assert principal.user_id in params.values()
            assert "LIMIT" in str(query) and "OFFSET" in str(query)
            return SimpleNamespace(all=lambda: [row])

    result = await list_notifications(20, 0, principal, Session())
    assert result[0]["conversation_id"] == str(row.conversation_id)
    assert set(result[0]) == {
        "id",
        "conversation_id",
        "message_id",
        "title",
        "body",
        "preview_mode",
    }
