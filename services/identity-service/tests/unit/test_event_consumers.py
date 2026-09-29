import uuid

import pytest

from app.events.consumers import apply_membership_event


class Db:
    async def scalar(self, _):
        return object()


@pytest.mark.asyncio
async def test_duplicate_membership_event_is_ignored():
    event = {"event_id": str(uuid.uuid4()), "event_type": "member.activated.v1", "payload": {}}
    assert await apply_membership_event(Db(), event) is False
