from uuid import uuid4

import pytest
from rest_framework.test import APIClient

from apps.organizations.services import provision_organization
from common.authorization import PERMISSIONS
from common.context import TenantContext


@pytest.fixture
def tenants(db, settings):
    settings.DEV_CONTEXT_ENABLED = True
    settings.REST_FRAMEWORK = {**settings.REST_FRAMEWORK, "DEFAULT_THROTTLE_CLASSES": []}
    a, owner_a = provision_organization(
        name="Alpha", slug="alpha", owner_name="Owner A", owner_user_id=uuid4()
    )
    b, owner_b = provision_organization(
        name="Beta", slug="beta", owner_name="Owner B", owner_user_id=uuid4()
    )
    return a, owner_a, b, owner_b


@pytest.fixture
def context(tenants):
    a, owner, _, _ = tenants
    return TenantContext(a.id, owner.id, owner.user_id, PERMISSIONS, "test-correlation")


@pytest.fixture
def client(tenants):
    api = APIClient()
    api.credentials(HTTP_X_DEV_MEMBER_ID=str(tenants[1].id), HTTP_X_CORRELATION_ID="api-test")
    return api
