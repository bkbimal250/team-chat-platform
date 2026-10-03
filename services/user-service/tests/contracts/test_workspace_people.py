import asyncio
import uuid
from types import SimpleNamespace

from app.main import User, search_users


def test_people_search_returns_tenant_member_id_without_frontend_translation():
    org, member_id, user_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    user = User(id=user_id, identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")

    class Session:
        async def execute(self, query):
            sql = str(query)
            assert "membership_projections.organization_id" in sql
            assert "membership_projections.status" in sql
            assert org in query.compile().params.values()
            return SimpleNamespace(all=lambda: [(user, member_id)])

    result = asyncio.run(
        search_users(
            q="Ad", limit=20, context=SimpleNamespace(organization_id=org), session=Session()
        )
    )
    assert result["users"][0]["member_id"] == str(member_id)
    assert result["users"][0]["user_id"] == str(user_id)
    assert result["users"][0]["member_id"] != result["users"][0]["user_id"]
