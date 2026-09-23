from django.utils import timezone

from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.roles.models import Role, RoleAssignment
from apps.roles.services import check_delegation
from apps.teams.services import add_membership
from common.exceptions import DomainError
from common.selectors import tenant_get
from common.services import command, lock_tenant, record, validate_fields, validate_relations


@command
def create_invitation(context, data):
    organization = lock_tenant(context, "invitation.create")
    if not organization.settings.allow_member_invites:
        raise DomainError("INVITES_DISABLED", "Member invitations are disabled.", 403)
    role = tenant_get(Role, context, data["intended_role_id"])
    check_delegation(context, role)
    if data["expires_at"] <= timezone.now():
        raise DomainError("INVALID_EXPIRY", "Invitation expiry must be in the future.", 400)
    invitation = Invitation(
        organization=organization, invited_by_member_id=context.member_id, **data
    )
    validate_relations(context, invitation)
    validate_fields(invitation)
    invitation.save()
    record(context, invitation, "invitation", "created")
    return invitation


@command
def revoke_invitation(context, pk):
    lock_tenant(context, "invitation.revoke")
    invitation = tenant_get(Invitation, context, pk, lock=True)
    if invitation.status == "REVOKED":
        return invitation
    if invitation.status != "PENDING":
        raise DomainError("INVITATION_NOT_PENDING", "Only pending invitations can be revoked.")
    invitation.status = "REVOKED"
    invitation.revoked_at = timezone.now()
    invitation.save()
    record(context, invitation, "invitation", "revoked")
    return invitation


@command
def accept_invitation(context, pk, member_id):
    """Trusted business command; no QR, token or credential handling."""
    lock_tenant(context, "invitation.accept")
    invitation = tenant_get(Invitation, context, pk, lock=True)
    if invitation.status == "ACCEPTED" and invitation.accepted_member_id == member_id:
        return invitation
    if invitation.status != "PENDING" or invitation.expires_at <= timezone.now():
        raise DomainError("INVITATION_UNAVAILABLE", "Invitation is no longer available.")
    member = tenant_get(Member, context, member_id, lock=True)
    if member.status != "ACTIVE":
        raise DomainError(
            "MEMBER_INACTIVE", "Invitation acceptance requires an active linked member."
        )
    check_delegation(context, invitation.intended_role)
    _, assigned = RoleAssignment.objects.get_or_create(
        organization_id=context.organization_id, member=member, role=invitation.intended_role
    )
    if assigned:
        record(context, member, "member", "role_changed", ["roles"])
    if invitation.team_id:
        add_membership(context, invitation.team_id, member.id)
    if invitation.branch_id:
        add_membership(context, invitation.branch_id, member.id, branch=True)
    invitation.status = "ACCEPTED"
    invitation.accepted_at = timezone.now()
    invitation.accepted_member = member
    invitation.save()
    record(context, invitation, "invitation", "accepted", ["status", "accepted_member_id"])
    return invitation
