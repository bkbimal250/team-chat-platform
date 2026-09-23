from django.utils import timezone

from apps.branches.models import Branch, BranchMembership
from apps.members.models import Member
from apps.teams.models import Team, TeamMembership
from common.exceptions import DomainError
from common.selectors import tenant_get
from common.services import command, lock_tenant, record, validate_fields


@command
def add_membership(context, parent_id, member_id, *, branch=False, role="MEMBER", is_primary=False):
    aggregate = "branch" if branch else "team"
    lock_tenant(context, f"{aggregate}.update")
    parent = tenant_get(Branch if branch else Team, context, parent_id, lock=True)
    member = tenant_get(Member, context, member_id, lock=True)
    if parent.status != "ACTIVE" or member.status != "ACTIVE":
        raise DomainError(
            "INACTIVE_MEMBERSHIP_TARGET", "Both the resource and member must be active."
        )
    model = BranchMembership if branch else TeamMembership
    values = (
        {"branch": parent, "is_primary": is_primary} if branch else {"team": parent, "role": role}
    )
    membership = model(organization_id=context.organization_id, member=member, **values)
    validate_fields(membership)
    membership.save()
    record(context, membership, f"{aggregate}_membership", "created")
    return membership


@command
def end_membership(context, parent_id, membership_id, *, branch=False):
    aggregate = "branch" if branch else "team"
    lock_tenant(context, f"{aggregate}.update")
    membership = tenant_get(
        BranchMembership if branch else TeamMembership, context, membership_id, lock=True
    )
    if getattr(membership, f"{aggregate}_id") != parent_id:
        from django.http import Http404

        raise Http404
    if membership.left_at:
        return membership
    membership.left_at = timezone.now()
    if branch:
        membership.is_primary = False
    else:
        membership.status = "LEFT"
    membership.save()
    record(context, membership, f"{aggregate}_membership", "left")
    return membership


@command
def set_primary_branch(context, membership_id):
    lock_tenant(context, "branch.update")
    membership = tenant_get(BranchMembership, context, membership_id, lock=True)
    if membership.left_at:
        raise DomainError("MEMBERSHIP_ENDED", "An ended membership cannot become primary.")
    tenant_get(Member, context, membership.member_id, lock=True)
    BranchMembership.objects.filter(
        organization_id=context.organization_id, member_id=membership.member_id, is_primary=True
    ).update(is_primary=False)
    membership.is_primary = True
    membership.save()
    record(context, membership, "branch_membership", "updated", ["is_primary"])
    return membership
