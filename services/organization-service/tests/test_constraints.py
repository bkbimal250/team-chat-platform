import pytest
from django.db import IntegrityError, transaction

from apps.audit.models import AuditLog
from apps.branches.models import Branch, BranchMembership
from apps.roles.models import Role, RoleAssignment, RolePermission
from apps.teams.models import Team, TeamMembership

pytestmark = pytest.mark.django_db


def rejects(operation):
    with pytest.raises(IntegrityError), transaction.atomic():
        operation()


def test_branch_code_scoping(tenants):
    a, _, b, _ = tenants
    Branch.objects.create(organization=a, name="A", code="SAME", country="IN")
    rejects(
        lambda: Branch.objects.create(organization=a, name="Duplicate", code="SAME", country="IN")
    )
    Branch.objects.create(organization=b, name="B", code="SAME", country="IN")


def test_unique_memberships_and_primary(tenants):
    a, member, _, _ = tenants
    branch = Branch.objects.create(organization=a, name="One", code="ONE", country="IN")
    branch2 = Branch.objects.create(organization=a, name="Two", code="TWO", country="IN")
    BranchMembership.objects.create(organization=a, branch=branch, member=member, is_primary=True)
    rejects(lambda: BranchMembership.objects.create(organization=a, branch=branch, member=member))
    rejects(
        lambda: BranchMembership.objects.create(
            organization=a, branch=branch2, member=member, is_primary=True
        )
    )
    team = Team.objects.create(organization=a, name="Team")
    TeamMembership.objects.create(organization=a, team=team, member=member)
    rejects(lambda: TeamMembership.objects.create(organization=a, team=team, member=member))


def test_cross_tenant_foreign_keys_even_bulk_operations(tenants):
    a, member, b, other = tenants
    team = Team.objects.create(organization=b, name="Other")
    branch = Branch.objects.create(organization=b, name="Other", code="B", country="IN")
    role = Role.objects.get(organization=b, kind="MEMBER")
    rejects(
        lambda: TeamMembership.objects.bulk_create(
            [TeamMembership(organization=a, team=team, member=member)]
        )
    )
    rejects(lambda: Team.objects.create(organization=a, name="Invalid", branch=branch))
    rejects(lambda: Team.objects.create(organization=a, name="Invalid", created_by_member=other))
    rejects(lambda: BranchMembership.objects.create(organization=a, branch=branch, member=member))
    rejects(lambda: RoleAssignment.objects.create(organization=a, member=member, role=role))
    rejects(
        lambda: RolePermission.objects.create(
            organization=a, role=role, permission=role.permissions.first()
        )
    )
    rejects(lambda: Team.objects.filter(id=team.id).update(organization=a))


def test_audit_is_append_only(tenants):
    row = AuditLog.objects.first()
    rejects(lambda: AuditLog.objects.filter(id=row.id).update(action="TAMPER"))
    rejects(lambda: AuditLog.objects.filter(id=row.id).delete())


def test_invalid_enum_rejected(tenants):
    rejects(lambda: Team.objects.create(organization=tenants[0], name="Bad", status="INVALID"))
