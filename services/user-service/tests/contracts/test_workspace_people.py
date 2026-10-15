import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from app.main import User, search_users


def test_people_search_returns_tenant_member_id_without_frontend_translation():
    org, member_id, user_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()
    identity_id = uuid.uuid4()
    user = User(id=user_id, identity_id=identity_id, display_name="Ada", status="ACTIVE")
    privacy = SimpleNamespace(profile_photo_visibility="ORGANIZATION", about_visibility="ORGANIZATION")

    class Session:
        async def scalar(self, query):
            return SimpleNamespace()

        async def execute(self, query):
            sql = str(query)
            assert "membership_projections.organization_id" in sql
            assert "membership_projections.status" in sql
            assert org in query.compile().params.values()
            return SimpleNamespace(all=lambda: [(user, member_id, privacy)])

    request = MagicMock()
    request.client = SimpleNamespace(host="127.0.0.1")
    request.app.state.contact_redis = AsyncMock()
    request.app.state.contact_redis.eval = AsyncMock(return_value=0)

    result = asyncio.run(
        search_users(
            request,
            q="Ad",
            limit=20,
            context=SimpleNamespace(
                organization_id=org, member_id=member_id, identity_id=identity_id
            ),
            session=Session(),
        )
    )
    assert result["users"][0]["member_id"] == str(member_id)
    assert result["users"][0]["user_id"] == str(user_id)
    assert result["users"][0]["member_id"] != result["users"][0]["user_id"]
