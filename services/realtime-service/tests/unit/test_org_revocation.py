from uuid import uuid4

import pytest

from app.auth import Principal
from app.events import EventConsumer
from app.org_membership import OrgMembershipStore
from app.registry import Registry


@pytest.mark.asyncio
async def test_member_removed_revokes_workspace_subscriptions():
    store = OrgMembershipStore()
    registry = Registry(membership_store=store)
    org = uuid4()
    member = uuid4()
    personal = await registry.register(Principal(uuid4(), uuid4(), uuid4(), None, uuid4()))
    workspace = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, member))
    conversation = uuid4()
    await registry.subscribe(workspace, conversation)
    await registry.subscribe(personal, uuid4())

    event = {
        "event_id": str(uuid4()),
        "event_type": "member.removed.v2",
        "organization_id": str(org),
        "payload": {"member_id": str(member), "status": "REMOVED"},
    }
    assert await EventConsumer(registry).process(event)
    assert conversation not in workspace.subscriptions
    assert personal.subscriptions
    assert not await store.is_active(org, member)


@pytest.mark.asyncio
async def test_member_reactivated_does_not_restore_subscriptions():
    store = OrgMembershipStore()
    registry = Registry(membership_store=store)
    org, member = uuid4(), uuid4()
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, member))
    conversation = uuid4()
    await registry.subscribe(connection, conversation)
    await registry.revoke_workspace_member(org, member, "REMOVED")
    assert not connection.subscriptions

    event = {
        "event_id": str(uuid4()),
        "event_type": "member.reactivated.v2",
        "organization_id": str(org),
        "payload": {"member_id": str(member), "status": "ACTIVE"},
    }
    assert await EventConsumer(registry).process(event)
    assert await store.is_active(org, member)
    assert conversation not in connection.subscriptions


@pytest.mark.asyncio
async def test_inactive_member_excluded_from_message_recipients():
    store = OrgMembershipStore()
    registry = Registry(membership_store=store)
    org, member = uuid4(), uuid4()
    connection = await registry.register(Principal(uuid4(), uuid4(), uuid4(), org, member))
    conversation = uuid4()
    await registry.subscribe(connection, conversation)
    await store.set_status(org, member, "REMOVED")

    recipients = await registry.recipients(org, conversation)
    assert recipients == []
