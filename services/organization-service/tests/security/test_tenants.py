from datetime import timedelta

import pytest
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.branches.models import Branch
from apps.invitations.models import Invitation
from apps.roles.models import Role
from apps.teams.models import Team


@pytest.mark.django_db
def test_direct_cross_tenant_access(client, tenants):
    _, _, other, member = tenants
    branch = Branch.objects.create(organization=other, name="Other", code="X", country="IN")
    team = Team.objects.create(organization=other, name="Other")
    for path in [f"branches/{branch.id}/", f"members/{member.id}/", f"teams/{team.id}/"]:
        response = client.get("/api/v1/" + path)
        assert response.status_code == 404
        assert response.data["error"]["correlation_id"] == "api-test"
    assert client.patch(f"/api/v1/branches/{branch.id}/", {"name": "Hacked"}).status_code == 404
    assert (
        client.post(
            f"/api/v1/teams/{team.id}/members/", {"member_id": str(tenants[1].id)}
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_indirect_cross_tenant_ids(client, tenants):
    a, owner, b, other_member = tenants
    other_branch = Branch.objects.create(organization=b, name="B", code="B", country="IN")
    team = Team.objects.create(organization=a, name="A")
    assert (
        client.post(
            "/api/v1/teams/", {"name": "Leak", "branch_id": str(other_branch.id)}
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/api/v1/teams/{team.id}/members/", {"member_id": str(other_member.id)}
        ).status_code
        == 404
    )
    response = client.post(
        "/api/v1/branches/",
        {"name": "X", "code": "X", "country": "IN", "organization_id": str(b.id)},
    )
    assert response.status_code == 400
    other_role = Role.objects.get(organization=b, kind="OWNER")
    assert (
        client.post(
            f"/api/v1/members/{owner.id}/roles/", {"role_id": str(other_role.id)}
        ).status_code
        == 404
    )


@pytest.mark.django_db
def test_collections_scoped(client, tenants):
    _, _, b, _ = tenants
    Invitation.objects.create(
        organization=b,
        intended_role=Role.objects.get(organization=b, kind="MEMBER"),
        expires_at=timezone.now() + timedelta(days=1),
    )
    response = client.get("/api/v1/invitations/")
    assert response.status_code == 200
    assert response.data["results"] == []
    audit = client.get("/api/v1/audit-logs/")
    assert audit.status_code == 200
    assert all(row["organization"] != str(b.id) for row in audit.data["results"])
    other_log = AuditLog.objects.filter(organization=b).first()
    assert client.get(f"/api/v1/audit-logs/{other_log.id}/").status_code == 404


@pytest.mark.django_db
def test_missing_identity_and_production_fail_closed(client, settings):
    client.credentials()
    assert client.get("/api/v1/members/").status_code == 401
    settings.DEV_CONTEXT_ENABLED = False
    assert (
        client.get(
            "/api/v1/members/", HTTP_X_DEV_MEMBER_ID="11111111-1111-1111-1111-111111111111"
        ).status_code
        == 401
    )


@pytest.mark.django_db
def test_identity_and_status_cannot_be_patched(client, tenants):
    response = client.patch(
        f"/api/v1/members/{tenants[1].id}/",
        {"user_id": str(tenants[3].user_id), "status": "ACTIVE"},
    )
    assert response.status_code == 400
