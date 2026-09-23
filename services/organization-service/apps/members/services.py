from apps.members.models import Member
from apps.roles.models import RoleAssignment
from common.exceptions import DomainError


def protect_last_owner(member: Member) -> None:
    if RoleAssignment.objects.filter(member=member, role__kind="OWNER").exists():
        others = RoleAssignment.objects.filter(
            organization_id=member.organization_id, role__kind="OWNER", member__status="ACTIVE"
        ).exclude(member=member)
        if not others.exists():
            raise DomainError("LAST_OWNER", "An organization must retain an active owner.")
