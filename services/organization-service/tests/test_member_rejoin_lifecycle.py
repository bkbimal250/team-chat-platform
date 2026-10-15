"""Join → assign → remove → deny access → re-invite → rejoin, plus multi-company isolation."""

from uuid import uuid4

import pytest
from django.test import Client

from apps.branches.models import Branch, BranchMembership
from apps.invitations.onboarding import accept_bound
from apps.invitations.services import create_invitation
from apps.members.models import Member
from apps.organizations.services import provision_organization
from apps.roles.models import Role, RoleAssignment
from apps.teams.models import Team, TeamMembership
from common.services import transition
from events.outbox.models import OutboxEvent

pytestmark = pytest.mark.django_db
PHONE = "+919000000099"
SERVICE_TOKEN = "test-internal-service-token-32chars-min"


def invite(context, branch_id=None, team_id=None, role_kind="MEMBER"):
    role = Role.objects.get(organization_id=context.organization_id, kind=role_kind)
    return create_invitation(
        context,
        {
            "recipient_name": "Returning Employee",
            "recipient_phone": PHONE,
            "intended_role_id": role.id,
            "branch_id": branch_id,
            "team_id": team_id,
        },
    )


def test_member_rejoin_lifecycle_and_multi_company_isolation(context, settings):
    settings.INTERNAL_SERVICE_TOKEN = SERVICE_TOKEN
    identity = uuid4()
    branch = Branch.objects.create(
        organization_id=context.organization_id, name="HQ", code="HQ", country="IN"
    )
    team = Team.objects.create(organization_id=context.organization_id, name="Ops", branch=branch)
    admin_role = Role.objects.get(organization_id=context.organization_id, kind="ADMIN")

    first_invite = invite(context, branch_id=branch.id, team_id=team.id)
    joined = accept_bound(
        first_invite.id, first_invite.token_hash, PHONE, identity, "rejoin-test-1"
    )
    member = Member.objects.get(id=joined["member_id"])
    assert member.status == "ACTIVE"
    assert RoleAssignment.objects.filter(member=member, role__kind="MEMBER").exists()
    assert TeamMembership.objects.filter(member=member, team=team, status="ACTIVE").exists()

    manager_role = Role.objects.create(
        organization_id=context.organization_id, name="Ops Lead", kind="CUSTOM"
    )
    RoleAssignment.objects.create(
        organization_id=context.organization_id, member=member, role=manager_role
    )

    transition(context, Member, member.id, "REMOVED", "member")
    member.refresh_from_db()
    assert member.status == "REMOVED"
    assert member.user_id == identity
    assert not TeamMembership.objects.filter(member=member, status="ACTIVE").exists()
    assert OutboxEvent.objects.filter(
        aggregate_id=member.id, event_type="member.removed.v2"
    ).exists()

    client = Client()
    denied = client.get(
        f"/api/internal/v1/identity-memberships/{identity}/",
        HTTP_X_INTERNAL_SERVICE_TOKEN=SERVICE_TOKEN,
    )
    assert denied.status_code == 200
    assert denied.json()["memberships"] == []

    other_org, other_owner = provision_organization(
        name="Other Co",
        slug="other-" + uuid4().hex[:8],
        owner_name="Owner",
        owner_user_id=identity,
        organization_id=uuid4(),
        email="other@example.test",
        correlation_id="rejoin-multi",
    )
    assert Member.objects.filter(organization=other_org, user_id=identity, status="ACTIVE").exists()

    new_branch = Branch.objects.create(
        organization_id=context.organization_id, name="Remote", code="REM", country="IN"
    )
    new_team = Team.objects.create(
        organization_id=context.organization_id, name="Support", branch=new_branch
    )
    second_invite = invite(context, branch_id=new_branch.id, team_id=new_team.id, role_kind="ADMIN")
    rejoined = accept_bound(
        second_invite.id, second_invite.token_hash, PHONE, identity, "rejoin-test-2"
    )
    assert rejoined["member_id"] == str(member.id)
    member.refresh_from_db()
    assert member.status == "ACTIVE"
    assert member.id == member.id
    assert not RoleAssignment.objects.filter(member=member, role=manager_role).exists()
    assert RoleAssignment.objects.filter(member=member, role__kind="ADMIN").exists()
    assert not TeamMembership.objects.filter(member=member, team=team, status="ACTIVE").exists()
    assert TeamMembership.objects.filter(member=member, team=new_team, status="ACTIVE").exists()
    assert BranchMembership.objects.filter(
        member=member, branch=new_branch, left_at__isnull=True
    ).exists()
    assert OutboxEvent.objects.filter(
        aggregate_id=member.id, event_type="member.reactivated.v2"
    ).exists()
    payload = OutboxEvent.objects.filter(
        aggregate_id=member.id, event_type="member.reactivated.v2"
    ).latest("created_at").payload
    assert payload["user_id"] == str(identity)
    assert payload["identity_id"] == str(identity)

    allowed = client.get(
        f"/api/internal/v1/identity-memberships/{identity}/",
        HTTP_X_INTERNAL_SERVICE_TOKEN=SERVICE_TOKEN,
    )
    org_ids = {row["organization_id"] for row in allowed.json()["memberships"]}
    assert str(context.organization_id) in org_ids
    assert str(other_org.id) in org_ids
