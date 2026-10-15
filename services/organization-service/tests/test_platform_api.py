from uuid import uuid4

import pytest
from django.test import Client

from apps.members.models import Member
from apps.organizations.services import provision_organization
from apps.roles.models import Role, RoleAssignment

pytestmark = pytest.mark.django_db


@pytest.fixture
def platform_client(monkeypatch):
    monkeypatch.setattr("apps.organizations.platform_api.authorize", lambda request: None)
    return Client()


def test_platform_owners_returns_all_owner_memberships(platform_client):
    organization, first_owner = provision_organization(
        name="Owner Test", slug="owner-test", owner_name="First Owner", owner_user_id=uuid4()
    )
    second_owner = Member.objects.create(
        organization=organization,
        display_name="Second Owner",
        user_id=uuid4(),
        status=Member.Status.ACTIVE,
    )
    RoleAssignment.objects.create(
        organization=organization,
        member=second_owner,
        role=Role.objects.get(organization=organization, kind=Role.Kind.OWNER),
    )

    response = platform_client.get(f"/api/v1/platform/organizations/{organization.id}/owners/")

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert {item["id"] for item in response.json()["items"]} == {str(first_owner.id), str(second_owner.id)}
    assert all("OWNER" in item["roles"] for item in response.json()["items"])


def test_platform_memberships_remain_scoped_to_organization(platform_client):
    identity_id = uuid4()
    alpha, alpha_owner = provision_organization(
        name="Alpha Scope", slug="alpha-scope", owner_name="Alpha", owner_user_id=identity_id
    )
    beta, _ = provision_organization(
        name="Beta Scope", slug="beta-scope", owner_name="Beta", owner_user_id=identity_id
    )

    scoped = platform_client.get(f"/api/v1/platform/organizations/{alpha.id}/memberships/")
    cross_org = platform_client.get(f"/api/v1/platform/identities/{identity_id}/memberships/")

    assert scoped.status_code == 200
    assert [row["organization_id"] for row in scoped.json()["items"]] == [str(alpha.id)]
    assert cross_org.status_code == 200
    assert {row["organization_id"] for row in cross_org.json()["items"]} == {str(alpha.id), str(beta.id)}
    assert scoped.json()["items"][0]["id"] == str(alpha_owner.id)


def test_platform_membership_contract_does_not_expose_invitation_secrets(platform_client):
    organization, _ = provision_organization(
        name="Safe Data", slug="safe-data", owner_name="Owner", owner_user_id=uuid4()
    )
    response = platform_client.get(f"/api/v1/platform/organizations/{organization.id}/memberships/")

    assert response.status_code == 200
    serialized = str(response.json())
    assert "token" not in serialized.lower()
    assert "password" not in serialized.lower()


def test_platform_security_summary_uses_authoritative_counts(platform_client):
    organization, owner = provision_organization(
        name="Security Facts", slug="security-facts", owner_name="Owner", owner_user_id=uuid4()
    )
    admin = Member.objects.create(
        organization=organization, display_name="Admin", user_id=uuid4(), status=Member.Status.ACTIVE
    )
    suspended = Member.objects.create(
        organization=organization, display_name="Suspended", user_id=uuid4(), status=Member.Status.SUSPENDED
    )
    RoleAssignment.objects.create(
        organization=organization,
        member=admin,
        role=Role.objects.get(organization=organization, kind=Role.Kind.ADMIN),
    )

    response = platform_client.get(f"/api/v1/platform/organizations/{organization.id}/security/")

    assert response.status_code == 200
    assert response.json() == {
        "owners": 1,
        "administrators": 1,
        "active_members": 2,
        "inactive_members": 1,
        "member_statuses": {"ACTIVE": 2, "SUSPENDED": 1},
        "invitation_statuses": {},
    }
    assert str(suspended.id) not in str(response.json())
    assert str(owner.user_id) not in str(response.json())
