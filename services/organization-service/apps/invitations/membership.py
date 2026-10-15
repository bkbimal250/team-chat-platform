"""Invitation-driven membership changes, including safe rejoin after departure."""

from django.utils import timezone

from apps.branches.models import BranchMembership
from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.roles.models import RoleAssignment
from apps.teams.models import TeamMembership
from common.context import TenantContext
from common.exceptions import DomainError
from common.services import enforce_capacity, record

DEPARTED_MEMBER_STATUSES = frozenset({Member.Status.LEFT, Member.Status.REMOVED})


def assign_invitation_placements(context: TenantContext, invitation: Invitation, member: Member) -> None:
    if invitation.branch_id:
        exists = BranchMembership.objects.filter(
            organization_id=context.organization_id,
            member=member,
            branch_id=invitation.branch_id,
            left_at__isnull=True,
        ).exists()
        if not exists:
            membership = BranchMembership.objects.create(
                organization_id=context.organization_id,
                member=member,
                branch_id=invitation.branch_id,
            )
            record(context, membership, "branch_membership", "created")
    if invitation.team_id:
        exists = TeamMembership.objects.filter(
            organization_id=context.organization_id,
            member=member,
            team_id=invitation.team_id,
            status="ACTIVE",
        ).exists()
        if not exists:
            membership = TeamMembership.objects.create(
                organization_id=context.organization_id,
                member=member,
                team_id=invitation.team_id,
            )
            record(context, membership, "team_membership", "created")


def replace_role_from_invitation(context: TenantContext, invitation: Invitation, member: Member) -> None:
    RoleAssignment.objects.filter(
        organization_id=context.organization_id, member=member
    ).delete()
    RoleAssignment.objects.create(
        organization_id=context.organization_id, member=member, role=invitation.intended_role
    )
    record(context, member, "member", "role_changed", ["roles"])


def create_member_from_invitation(
    context: TenantContext, invitation: Invitation, identity_id
) -> Member:
    organization = invitation.organization
    enforce_capacity(organization, Member)
    member = Member.objects.create(
        organization=organization,
        user_id=identity_id,
        display_name=invitation.recipient_name,
        status=Member.Status.ACTIVE,
        joined_at=timezone.now(),
    )
    record(context, member, "member", "created")
    record(context, member, "member", "activated", ["status"])
    replace_role_from_invitation(context, invitation, member)
    assign_invitation_placements(context, invitation, member)
    return member


def rejoin_member_from_invitation(
    context: TenantContext, invitation: Invitation, member: Member
) -> Member:
    if member.status not in DEPARTED_MEMBER_STATUSES:
        raise DomainError("MEMBER_INACTIVE", "Contact your administrator about this membership.", 403)
    member.status = Member.Status.ACTIVE
    member.suspended_at = None
    member.left_at = None
    member.joined_at = member.joined_at or timezone.now()
    member.display_name = invitation.recipient_name
    member.save(
        update_fields=["status", "suspended_at", "left_at", "joined_at", "display_name", "updated_at"]
    )
    record(context, member, "member", "reactivated", ["status"])
    replace_role_from_invitation(context, invitation, member)
    assign_invitation_placements(context, invitation, member)
    return member
