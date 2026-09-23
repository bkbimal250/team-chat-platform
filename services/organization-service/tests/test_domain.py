from datetime import timedelta
from unittest.mock import patch
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.invitations.models import Invitation
from apps.invitations.services import accept_invitation
from apps.members.models import Member
from apps.organizations.services import set_organization_status
from apps.roles.models import Role
from apps.teams.models import Team
from common.exceptions import DomainError
from common.services import create_resource, transition
from events.outbox.models import OutboxEvent

pytestmark = pytest.mark.django_db


def test_atomic_audit_outbox(context):
    team = create_resource(context, Team, {"name": "Operations"}, "team")
    event = OutboxEvent.objects.get(aggregate_id=team.id)
    assert event.event_type == "team.created.v1"
    assert event.correlation_id == context.correlation_id
    assert AuditLog.objects.filter(resource_id=team.id).count() == 1


def test_rollback_when_outbox_fails(context):
    before = OutboxEvent.objects.count()
    with patch("common.services.OutboxEvent.objects.create", side_effect=RuntimeError("fail")):
        with pytest.raises(RuntimeError):
            create_resource(context, Team, {"name": "Rollback"}, "team")
    assert not Team.objects.filter(name="Rollback").exists()
    assert not AuditLog.objects.filter(resource_type="team").exists()
    assert OutboxEvent.objects.count() == before


def test_member_lifecycle_and_last_owner(context, tenants):
    member = create_resource(
        context, Member, {"display_name": "Employee", "user_id": uuid4()}, "member"
    )
    assert transition(context, Member, member.id, "ACTIVE", "member").joined_at
    assert transition(context, Member, member.id, "SUSPENDED", "member").suspended_at
    assert transition(context, Member, member.id, "REMOVED", "member").left_at
    with pytest.raises(DomainError, match="transition"):
        transition(context, Member, member.id, "ACTIVE", "member")
    with pytest.raises(DomainError) as exc:
        transition(context, Member, tenants[1].id, "REMOVED", "member")
    assert exc.value.machine_code == "LAST_OWNER"


def test_organization_lifecycle(context):
    assert set_organization_status(context, "SUSPENDED").suspended_at
    assert set_organization_status(context, "DISABLED", operator=True).status == "DISABLED"
    assert set_organization_status(context, "DELETED", operator=True).deleted_at
    with pytest.raises(DomainError):
        set_organization_status(context, "ACTIVE", operator=True)


def test_expired_invitation_cannot_be_accepted(context, tenants):
    invitation = Invitation.objects.create(
        organization=tenants[0],
        intended_role=Role.objects.get(organization=tenants[0], kind="MEMBER"),
        expires_at=timezone.now() - timedelta(seconds=1),
    )
    with pytest.raises(DomainError) as exc:
        accept_invitation(context, invitation.id, tenants[1].id)
    assert exc.value.machine_code == "INVITATION_UNAVAILABLE"


def test_capacity_enforced(context, tenants):
    settings = tenants[0].settings
    settings.max_teams = 0
    settings.save()
    with pytest.raises(DomainError) as exc:
        create_resource(context, Team, {"name": "Too many"}, "team")
    assert exc.value.machine_code == "TENANT_LIMIT_REACHED"
