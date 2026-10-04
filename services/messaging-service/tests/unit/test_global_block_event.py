import uuid

import pytest

from app.events import apply_projection
from app.models import BlockProjection


@pytest.mark.asyncio
async def test_global_block_event_uses_identity_ids_without_tenant_id():
    class Session:
        added = []

        async def scalar(self, *_):
            return None

        def add(self, item):
            self.added.append(item)

    blocker, blocked = uuid.uuid4(), uuid.uuid4()
    session = Session()
    await apply_projection(
        session,
        {
            "event_id": str(uuid.uuid4()),
            "event_type": "user.blocked.v1",
            "organization_id": None,
            "producer": "user-service",
            "payload": {
                "blocker_user_id": str(uuid.uuid4()),
                "blocked_user_id": str(uuid.uuid4()),
                "blocker_identity_id": str(blocker),
                "blocked_identity_id": str(blocked),
            },
        },
    )
    row = next(item for item in session.added if isinstance(item, BlockProjection))
    assert row.blocker_user_id == blocker
    assert row.blocked_user_id == blocked
