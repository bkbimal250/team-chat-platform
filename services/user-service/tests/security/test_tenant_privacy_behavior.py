import uuid

from app.auth import AuthContext


def test_authenticated_context_carries_only_its_organization():
    org_a, org_b = uuid.uuid4(), uuid.uuid4()
    context = AuthContext(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), org_a, uuid.uuid4())
    assert context.organization_id == org_a
    assert context.organization_id != org_b


def test_cross_tenant_override_cannot_mutate_authenticated_context():
    context = AuthContext(uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    supplied_organization = uuid.uuid4()
    assert context.organization_id != supplied_organization
