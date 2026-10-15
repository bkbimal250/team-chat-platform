"""Real PostgreSQL invitation authorization, token lifecycle and acceptance tests."""

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from uuid import uuid4

import pytest
from django.db import connections
from django.utils import timezone

from apps.branches.models import Branch, BranchMembership
from apps.invitations.models import Invitation
from apps.invitations.onboarding import accept_bound, available
from apps.invitations.services import create_invitation, resend_invitation, revoke_invitation
from apps.members.models import Member
from apps.roles.models import Role, RoleAssignment
from apps.teams.models import Team, TeamMembership
from common.authorization import effective_permissions
from common.context import TenantContext
from common.exceptions import DomainError
from common.serializers import InvitationSerializer
from events.outbox.models import OutboxEvent

pytestmark = pytest.mark.django_db
PHONE = "+919000000003"


def invite(context, **extra):
    role = Role.objects.get(organization_id=context.organization_id, kind="MEMBER")
    return create_invitation(
        context,
        {
            "recipient_name": "Invited Employee",
            "recipient_phone": PHONE,
            "intended_role_id": role.id,
            **extra,
        },
    )


def token(row):
    return row.development_url.split("#invite=")[1]


def accept(row, identity_id=None, **extra):
    return accept_bound(
        row.id, row.token_hash, row.recipient_phone, identity_id or uuid4(), "test-accept", **extra
    )


def test_opaque_hashed_token_and_private_serialization(context, client, caplog):
    row = invite(context)
    secret = token(row)
    assert len(secret) >= 32 and secret not in str(row.id)
    row.refresh_from_db()
    assert row.token_hash == hashlib.sha256(secret.encode()).hexdigest()
    assert "token_hash" not in InvitationSerializer(row).data
    assert "development_url" not in client.get(f"/api/v1/invitations/{row.id}/").json()
    assert secret not in caplog.text and PHONE not in caplog.text
    assert row.expires_at <= timezone.now() + timedelta(hours=48)


def test_new_member_exact_assignments_and_idempotent_acceptance(context):
    branch = Branch.objects.create(
        organization_id=context.organization_id, name="Local", code="L", country="IN"
    )
    team = Team.objects.create(organization_id=context.organization_id, name="Staff", branch=branch)
    row = invite(context, branch_id=branch.id, team_id=team.id)
    identity = uuid4()
    first = accept(row, identity)
    before_events = OutboxEvent.objects.count()
    assert accept(row, identity) == first
    assert OutboxEvent.objects.count() == before_events
    member = Member.objects.get(id=first["member_id"])
    row.refresh_from_db()
    assert row.status == "ACCEPTED" and row.accepted_at and row.accepted_member == member
    assert member.user_id == identity and member.status == "ACTIVE"
    assert RoleAssignment.objects.filter(member=member, role=row.intended_role).count() == 1
    assert BranchMembership.objects.filter(member=member, branch=branch).count() == 1
    assert TeamMembership.objects.filter(member=member, team=team).count() == 1
    assert set(
        OutboxEvent.objects.filter(aggregate_id=member.id).values_list("event_type", flat=True)
    ) == {"member.created.v2", "member.activated.v2", "member.role_changed.v2"}
    with pytest.raises(DomainError):
        accept(row, uuid4())


def test_existing_membership_preserved_without_role_elevation(context):
    row = invite(context)
    owner = Member.objects.get(id=context.member_id)
    roles = list(owner.role_assignments.values_list("role_id", flat=True))
    result = accept(row, owner.user_id)
    assert result["member_id"] == str(owner.id)
    assert list(owner.role_assignments.values_list("role_id", flat=True)) == roles
    assert owner.display_name == "Owner A"


@pytest.mark.parametrize("state", ["REVOKED", "EXPIRED", "ACCEPTED", "expired-clock"])
def test_unavailable_token_never_creates_membership(context, state):
    row = invite(context)
    if state == "expired-clock":
        row.expires_at = timezone.now() - timedelta(seconds=1)
    else:
        row.status = state
    row.save()
    before = Member.objects.count()
    with pytest.raises(DomainError):
        available(row)
    with pytest.raises(DomainError):
        accept(row)
    assert Member.objects.count() == before


@pytest.mark.parametrize("field", ["phone", "token_hash", "invitation_id"])
def test_wrong_binding_rejected(context, field):
    row = invite(context)
    values = {
        "invitation_id": row.id,
        "token_hash": row.token_hash,
        "phone": PHONE,
        "identity_id": uuid4(),
        "correlation_id": "test",
    }
    values[field] = uuid4() if field == "invitation_id" else "wrong"
    with pytest.raises(DomainError):
        accept_bound(**values)
    row.refresh_from_db()
    assert row.status == "PENDING"


def test_resend_rotates_and_revoke_invalidates(context):
    row = invite(context)
    old = row.token_hash
    rotated = resend_invitation(context, row.id)
    assert rotated.token_hash != old
    with pytest.raises(DomainError):
        accept_bound(row.id, old, PHONE, uuid4(), "test")
    revoked = revoke_invitation(context, row.id)
    with pytest.raises(DomainError):
        accept(revoked)


def test_duplicate_pending_and_active_member_controlled(context):
    row = invite(context)
    with pytest.raises(DomainError) as error:
        invite(context)
    assert error.value.machine_code == "INVITATION_PENDING"
    accept(row)
    with pytest.raises(DomainError) as error:
        invite(context)
    assert error.value.machine_code == "MEMBER_ALREADY_EXISTS"


def test_same_phone_other_tenant_and_fresh_after_expiry(context, tenants):
    row = invite(context)
    other = tenants[3]
    second = TenantContext(
        other.organization_id, other.id, other.user_id, effective_permissions(other), "test"
    )
    assert invite(second).organization_id != row.organization_id
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save()
    assert invite(context).id != row.id


@pytest.mark.parametrize(
    "field",
    [
        "organization",
        "organization_id",
        "invited_by_member",
        "token_hash",
        "accepted_member",
        "status",
    ],
)
def test_client_cannot_spoof_authority(context, client, field):
    role = Role.objects.get(organization_id=context.organization_id, kind="MEMBER")
    result = client.post(
        "/api/v1/invitations/",
        {
            "recipient_name": "Employee",
            "recipient_phone": PHONE,
            "intended_role_id": str(role.id),
            field: str(uuid4()),
        },
        format="json",
    )
    assert result.status_code == 400


def test_cross_tenant_lookup_revoke_and_target_rejected(context, tenants, client):
    other = tenants[3]
    foreign = TenantContext(
        other.organization_id, other.id, other.user_id, effective_permissions(other), "test"
    )
    row = invite(foreign)
    assert client.get(f"/api/v1/invitations/{row.id}/").status_code == 404
    assert client.post(f"/api/v1/invitations/{row.id}/revoke/").status_code == 404
    foreign_role = Role.objects.get(organization_id=other.organization_id, kind="MEMBER")
    assert (
        client.post(
            "/api/v1/invitations/",
            {
                "recipient_name": "Employee",
                "recipient_phone": PHONE,
                "intended_role_id": str(foreign_role.id),
            },
            format="json",
        ).status_code
        == 404
    )


@pytest.mark.parametrize(
    "kind,expected", [("OWNER", 201), ("ADMIN", 201), ("MANAGER", 201), ("MEMBER", 403)]
)
def test_actual_inviter_permissions(tenants, client, kind, expected):
    org, owner, _, _ = tenants
    if kind != "OWNER":
        member = Member.objects.create(
            organization=org, user_id=uuid4(), display_name="Inviter", status="ACTIVE"
        )
        RoleAssignment.objects.create(
            organization=org, member=member, role=Role.objects.get(organization=org, kind=kind)
        )
        client.credentials(HTTP_X_DEV_MEMBER_ID=str(member.id))
    result = client.post(
        "/api/v1/invitations/",
        {
            "recipient_name": "Employee",
            "recipient_phone": PHONE,
            "intended_role_id": str(Role.objects.get(organization=org, kind="MEMBER").id),
        },
        format="json",
    )
    assert result.status_code == expected


def test_legacy_accept_cannot_bypass_phone_otp(context, client):
    row = invite(context)
    assert (
        client.post(
            f"/api/v1/invitations/{row.id}/accept/",
            {"member_id": str(context.member_id)},
            format="json",
        ).status_code
        == 403
    )


def test_internal_route_requires_service_identity(client):
    assert (
        client.post(
            "/api/internal/v1/invitations/validate/", {"token": "a" * 43}, format="json"
        ).status_code
        == 401
    )


def test_expired_list_and_token_lookup(context, client, settings):
    settings.INTERNAL_SERVICE_TOKEN = "local-test-service"
    row = invite(context)
    row.expires_at = timezone.now() - timedelta(seconds=1)
    row.save()
    assert (
        client.get("/api/v1/invitations/?status=EXPIRED").json()["results"][0]["status"]
        == "EXPIRED"
    )
    for secret in ["a" * 43, token(row)]:
        result = client.post(
            "/api/internal/v1/invitations/validate/",
            {"token": secret},
            format="json",
            HTTP_X_INTERNAL_SERVICE_TOKEN="local-test-service",
        )
        assert result.status_code in {404, 410}


@pytest.mark.django_db(transaction=True)
def test_parallel_acceptance_one_membership(context):
    row = invite(context)
    identity = uuid4()

    def run():
        connections.close_all()
        try:
            return accept_bound(row.id, row.token_hash, PHONE, identity, "parallel")
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as executor:
        first, second = list(executor.map(lambda _: run(), range(2)))
    assert first == second
    assert (
        Member.objects.filter(organization_id=context.organization_id, user_id=identity).count()
        == 1
    )


def test_production_delivery_fails_closed(context, settings):
    settings.ENVIRONMENT = "production"
    with pytest.raises(DomainError) as error:
        invite(context)
    assert error.value.machine_code == "DELIVERY_UNAVAILABLE"
    assert not Invitation.objects.filter(recipient_phone=PHONE).exists()


@pytest.mark.parametrize("kind", ["ADMIN", "MANAGER"])
def test_inviter_cannot_delegate_owner_role(tenants, client, kind):
    org = tenants[0]
    inviter = Member.objects.create(
        organization=org, user_id=uuid4(), display_name="Delegator", status="ACTIVE"
    )
    RoleAssignment.objects.create(
        organization=org, member=inviter, role=Role.objects.get(organization=org, kind=kind)
    )
    client.credentials(HTTP_X_DEV_MEMBER_ID=str(inviter.id))
    response = client.post(
        "/api/v1/invitations/",
        {
            "recipient_name": "Employee",
            "recipient_phone": PHONE,
            "intended_role_id": str(Role.objects.get(organization=org, kind="OWNER").id),
        },
        format="json",
    )
    assert response.status_code == 403 and not Invitation.objects.exists()


@pytest.mark.parametrize("change", ["inviter_suspended", "invites_disabled", "team_disabled"])
def test_acceptance_rechecks_current_authority_and_assignments(context, change):
    team = Team.objects.create(organization_id=context.organization_id, name="Assigned Team")
    row = invite(context, team_id=team.id)
    if change == "inviter_suspended":
        Member.objects.filter(id=context.member_id).update(status="SUSPENDED")
    elif change == "invites_disabled":
        settings = row.organization.settings
        settings.allow_member_invites = False
        settings.save()
    else:
        Team.objects.filter(id=team.id).update(status="DISABLED")
    before = Member.objects.count()
    with pytest.raises(DomainError):
        accept(row)
    assert Member.objects.count() == before and not TeamMembership.objects.exists()


def test_acceptance_and_outbox_roll_back_together(context, monkeypatch):
    row = invite(context)
    before = Member.objects.count()

    def failed_event(*args, **kwargs):
        raise RuntimeError("test outbox unavailable")

    monkeypatch.setattr("apps.invitations.onboarding.record", failed_event)
    with pytest.raises(RuntimeError):
        accept(row)
    row.refresh_from_db()
    assert row.status == "PENDING" and Member.objects.count() == before


@pytest.mark.parametrize("matching_identity", [True, False])
def test_private_resume_requires_accepted_phone_and_identity(
    context, client, settings, matching_identity
):
    settings.INTERNAL_SERVICE_TOKEN = "local-test-service"
    row = invite(context)
    identity = uuid4()
    accept(row, identity)
    body = {
        "invitation_id": str(row.id),
        "token_hash": row.token_hash,
        "phone": PHONE,
        "identity_id": str(identity if matching_identity else uuid4()),
    }
    path = "/api/internal/v1/invitations/resume/"
    assert client.post(path, body, format="json").status_code == 401
    response = client.post(
        path, body, format="json", HTTP_X_INTERNAL_SERVICE_TOKEN="local-test-service"
    )
    assert response.status_code == (200 if matching_identity else 404)
    if matching_identity:
        assert response.json()["organization_id"] == str(context.organization_id)
    assert (
        Member.objects.filter(organization_id=context.organization_id, user_id=identity).count()
        == 1
    )


def test_email_invitation_without_phone_keeps_authoritative_assignments(context):
    row = invite(context, recipient_phone="", recipient_email=" Employee@Example.test ")
    assert row.recipient_email == "employee@example.test"
    assert row.recipient_phone == ""
    identity = uuid4()
    result = accept_bound(
        row.id, row.token_hash, None, identity, "email-test", email=row.recipient_email
    )
    assert Member.objects.get(id=result["member_id"]).user_id == identity
    assert (
        accept_bound(row.id, row.token_hash, None, identity, "retry", email=row.recipient_email)
        == result
    )


def test_email_invitation_rejects_wrong_recipient(context):
    row = invite(context, recipient_phone="", recipient_email="employee@example.test")
    with pytest.raises(DomainError):
        accept_bound(
            row.id, row.token_hash, None, uuid4(), "email-test", email="other@example.test"
        )
    row.refresh_from_db()
    assert row.status == "PENDING"
