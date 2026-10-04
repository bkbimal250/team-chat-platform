import json
from uuid import uuid4

import pytest

from apps.members.models import Member
from apps.organizations.models import Organization
from apps.roles.models import RoleAssignment
from common.authorization import effective_permissions


@pytest.mark.django_db(transaction=True)
def test_internal_company_registration_is_atomic_idempotent_and_owner(client, settings):
    settings.INTERNAL_SERVICE_TOKEN = "test-internal"
    data = {
        "organization_id": str(uuid4()),
        "identity_id": str(uuid4()),
        "company_name": "Registration Company",
        "owner_name": "Owner",
        "email": "owner@example.test",
    }
    path = "/api/internal/v1/company-registration/"
    assert (
        client.post(path, data=json.dumps(data), content_type="application/json").status_code == 401
    )
    first = client.post(
        path,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal",
    )
    assert first.status_code == 200
    second = client.post(
        path,
        data=json.dumps(data),
        content_type="application/json",
        HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal",
    )
    assert second.json() == first.json()
    assert Organization.objects.filter(id=data["organization_id"]).count() == 1
    owner = Member.objects.get(organization_id=data["organization_id"])
    assert "member.create" in effective_permissions(owner)
    assert RoleAssignment.objects.filter(member=owner, role__kind="OWNER").count() == 1
    data["identity_id"] = str(uuid4())
    assert (
        client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal",
        ).status_code
        == 409
    )


@pytest.mark.django_db(transaction=True)
def test_invalid_owner_rolls_back_company(client, settings):
    settings.INTERNAL_SERVICE_TOKEN = "test-internal"
    data = {
        "organization_id": str(uuid4()),
        "identity_id": str(uuid4()),
        "company_name": "",
        "owner_name": "Owner",
        "email": "owner@example.test",
    }
    result = client.post(
        "/api/internal/v1/company-registration/",
        data=json.dumps(data),
        content_type="application/json",
        HTTP_X_INTERNAL_SERVICE_TOKEN="test-internal",
    )
    assert result.status_code == 409
    assert not Organization.objects.filter(id=data["organization_id"]).exists()
