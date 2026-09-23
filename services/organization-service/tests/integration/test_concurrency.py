from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier, Lock
from uuid import uuid4

import pytest
from django.db import connections
from django.utils import timezone

from apps.branches.models import Branch, BranchMembership
from apps.invitations.models import Invitation
from apps.invitations.services import accept_invitation
from apps.organizations.services import provision_organization
from apps.roles.models import Role
from apps.teams.models import Team, TeamMembership
from apps.teams.services import add_membership
from common.authorization import PERMISSIONS
from common.context import TenantContext
from common.exceptions import DomainError
from events.outbox.models import OutboxEvent
from events.outbox.worker import publish_one

pytestmark = pytest.mark.django_db(transaction=True)


@pytest.fixture
def concurrent_context():
    organization, owner = provision_organization(
        name="Concurrent", slug="concurrent", owner_name="Owner", owner_user_id=uuid4()
    )
    return TenantContext(organization.id, owner.id, owner.user_id, PERMISSIONS)


def race(operations):
    barrier = Barrier(len(operations))

    def run(operation):
        connections.close_all()
        try:
            barrier.wait(timeout=10)
            return operation()
        except DomainError as exc:
            return exc.machine_code
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=len(operations)) as executor:
        return list(executor.map(run, operations))


def test_concurrent_duplicate_membership(concurrent_context):
    context = concurrent_context
    team = Team.objects.create(organization_id=context.organization_id, name="Concurrent")
    results = race([lambda: add_membership(context, team.id, context.member_id)] * 2)
    assert sum(isinstance(result, TeamMembership) for result in results) == 1
    assert "TEAM_MEMBERSHIP_EXISTS" in results
    assert TeamMembership.objects.count() == 1
    assert OutboxEvent.objects.filter(event_type="team_membership.created.v1").count() == 1


def test_concurrent_primary_branches(concurrent_context):
    context = concurrent_context
    first = Branch.objects.create(
        organization_id=context.organization_id, name="A", code="A", country="IN"
    )
    second = Branch.objects.create(
        organization_id=context.organization_id, name="B", code="B", country="IN"
    )
    results = race(
        [
            lambda: add_membership(
                context, first.id, context.member_id, branch=True, is_primary=True
            ),
            lambda: add_membership(
                context, second.id, context.member_id, branch=True, is_primary=True
            ),
        ]
    )
    assert "PRIMARY_BRANCH_EXISTS" in results
    assert BranchMembership.objects.filter(is_primary=True).count() == 1


def test_concurrent_invitation_acceptance_is_idempotent(concurrent_context):
    context = concurrent_context
    invitation = Invitation.objects.create(
        organization_id=context.organization_id,
        intended_role=Role.objects.get(organization_id=context.organization_id, kind="MEMBER"),
        expires_at=timezone.now() + timedelta(days=1),
    )
    results = race([lambda: accept_invitation(context, invitation.id, context.member_id)] * 2)
    assert all(result.status == "ACCEPTED" for result in results)
    assert OutboxEvent.objects.filter(event_type="invitation.accepted.v1").count() == 1


def test_concurrent_publishers_do_not_publish_same_locked_row(concurrent_context):
    published = []
    mutex = Lock()

    class Publisher:
        def publish(self, event):
            with mutex:
                published.append(event.event_id)

    race([lambda: publish_one(Publisher())] * 2)
    assert len(published) == 2
    assert len(set(published)) == 2
