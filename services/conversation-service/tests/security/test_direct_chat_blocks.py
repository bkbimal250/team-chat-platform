import uuid
from unittest.mock import AsyncMock

import pytest

from app.core import DomainError
from app.services import ConversationService


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked", [True, False])
async def test_direct_chat_checks_active_members_and_blocks_before_existing_chat(blocked):
    org, actor, target, a, b = [uuid.uuid4() for _ in range(5)]
    service = ConversationService()
    service.member_user_id = AsyncMock(side_effect=[a, b])

    class Result:
        def scalar_one_or_none(self):
            return object()

    class Session:
        async def scalar(self, query):
            text = str(query)
            assert " OR " in text
            assert query.compile().params == {
                "blocker_user_id_1": a,
                "blocked_user_id_1": b,
                "blocker_user_id_2": b,
                "blocked_user_id_2": a,
            }
            return uuid.uuid4() if blocked else None

        async def execute(self, query):
            assert "conversations.organization_id" in str(query)
            return Result()

    if blocked:
        with pytest.raises(DomainError) as error:
            await service.direct(Session(), org, actor, target, "test")
        assert error.value.status == 403
    else:
        _, created = await service.direct(Session(), org, actor, target, "test")
        assert not created
    assert service.member_user_id.call_args_list[0].args[1:] == (org, actor)
    assert service.member_user_id.call_args_list[1].args[1:] == (org, target)
