from datetime import timedelta
from uuid import uuid4

import pytest
from django.utils import timezone

from apps.members.models import Member
from apps.roles.models import Role, RoleAssignment

pytestmark = pytest.mark.django_db


def test_organization_settings_and_updates(client, tenants):
    response = client.get("/api/v1/organizations/current/")
    assert response.status_code == 200
    assert response.data["id"] == str(tenants[0].id)
    assert (
        client.patch("/api/v1/organizations/current/", {"display_name": "New"}).status_code == 200
    )
    result = client.patch("/api/v1/organizations/current/settings/", {"max_members": 5})
    assert result.status_code == 200 and result.data["max_members"] == 5
    assert (
        client.patch("/api/v1/organizations/current/", {"timezone": "bad/zone"}).status_code == 400
    )


def test_resources_and_memberships(client, tenants):
    branch = client.post("/api/v1/branches/", {"name": "Mumbai", "code": "MUM", "country": "IN"})
    assert branch.status_code == 201, branch.data
    branch_id = branch.data["id"]
    team = client.post("/api/v1/teams/", {"name": "Sales", "branch_id": branch_id})
    assert team.status_code == 201, team.data
    team_id = team.data["id"]
    assert (
        client.patch(f"/api/v1/teams/{team_id}/", {"description": "Sales group"}).status_code == 200
    )
    member = client.post("/api/v1/members/", {"display_name": "Employee", "employee_code": "E1"})
    assert member.status_code == 201, member.data
    assert member.data["status"] == "INVITED"
    member_id = str(tenants[1].id)
    team_membership = client.post(f"/api/v1/teams/{team_id}/members/", {"member_id": member_id})
    assert team_membership.status_code == 201, team_membership.data
    branch_membership = client.post(
        f"/api/v1/branches/{branch_id}/members/", {"member_id": member_id, "is_primary": True}
    )
    assert branch_membership.status_code == 201, branch_membership.data
    assert (
        client.post(f"/api/v1/teams/{team_id}/members/", {"member_id": member_id}).status_code
        == 409
    )
    assert len(client.get(f"/api/v1/teams/{team_id}/members/").data["results"]) == 1
    assert (
        client.post(
            f"/api/v1/teams/{team_id}/members/{team_membership.data['id']}/leave/"
        ).status_code
        == 200
    )
    assert (
        client.post(
            f"/api/v1/branches/{branch_id}/members/{branch_membership.data['id']}/primary/"
        ).status_code
        == 200
    )
    assert (
        client.post(f"/api/v1/branches/{branch_id}/lifecycle/", {"status": "DISABLED"}).status_code
        == 200
    )


def test_invitation_lifecycle(client, tenants):
    role = Role.objects.get(organization=tenants[0], kind="MEMBER")
    data = {
        "intended_role_id": str(role.id),
        "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
    }
    response = client.post("/api/v1/invitations/", data)
    assert response.status_code == 201, response.data
    path = f"/api/v1/invitations/{response.data['id']}/revoke/"
    assert client.post(path).data["status"] == "REVOKED"
    assert client.post(path).status_code == 200
    response = client.post("/api/v1/invitations/", data)
    path = f"/api/v1/invitations/{response.data['id']}/accept/"
    result = client.post(path, {"member_id": str(tenants[1].id)})
    assert result.status_code == 200, result.data
    assert result.data["status"] == "ACCEPTED"
    assert client.post(path, {"member_id": str(tenants[1].id)}).status_code == 200


def test_roles_and_member_permissions(client, tenants):
    member = Member.objects.create(
        organization=tenants[0], display_name="Limited", user_id=uuid4(), status="ACTIVE"
    )
    role = Role.objects.get(organization=tenants[0], kind="MEMBER")
    assert (
        client.post(f"/api/v1/members/{member.id}/roles/", {"role_id": str(role.id)}).status_code
        == 200
    )
    response = client.post(
        "/api/v1/roles/", {"name": "Read audit", "permission_codes": ["audit.view"]}, format="json"
    )
    assert response.status_code == 201, response.data
    assert client.get("/api/v1/permissions/").status_code == 200
    assert client.get("/api/v1/role-assignments/").status_code == 200
    client.credentials(HTTP_X_DEV_MEMBER_ID=str(member.id))
    assert client.get("/api/v1/members/").status_code == 200
    assert (
        client.post("/api/v1/branches/", {"name": "No", "code": "NO", "country": "IN"}).status_code
        == 403
    )
    assert client.get("/api/v1/audit-logs/").status_code == 403


def test_admin_cannot_invite_owner(client, tenants):
    member = Member.objects.create(
        organization=tenants[0], display_name="Admin", user_id=uuid4(), status="ACTIVE"
    )
    RoleAssignment.objects.create(
        organization=tenants[0],
        member=member,
        role=Role.objects.get(organization=tenants[0], kind="ADMIN"),
    )
    client.credentials(HTTP_X_DEV_MEMBER_ID=str(member.id))
    owner_role = Role.objects.get(organization=tenants[0], kind="OWNER")
    result = client.post(
        "/api/v1/invitations/",
        {
            "intended_role_id": str(owner_role.id),
            "expires_at": (timezone.now() + timedelta(days=1)).isoformat(),
        },
    )
    assert result.status_code == 403


def test_filters_search_and_pagination(client, tenants):
    Member.objects.bulk_create(
        [Member(organization=tenants[0], display_name=f"Person {i}") for i in range(55)]
    )
    result = client.get("/api/v1/members/?search=Person&page_size=10&status=INVITED")
    assert result.status_code == 200
    assert len(result.data["results"]) == 10 and result.data["next"]
    page2 = client.get(result.data["next"])
    assert not {r["id"] for r in result.data["results"]} & {r["id"] for r in page2.data["results"]}


def test_health_schema_admin(client):
    assert client.get("/health/live").status_code == 200
    assert client.get("/health/ready").status_code == 200
    schema = client.get("/api/schema/?format=json")
    assert schema.status_code == 200
    assert "/api/v1/members/" in schema.data["paths"]
    assert client.get("/api/docs/").status_code == 200
    assert client.get("/admin/login/").status_code == 200
