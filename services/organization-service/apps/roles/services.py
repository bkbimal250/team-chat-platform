from apps.members.models import Member
from apps.members.services import protect_last_owner
from apps.roles.models import Permission, Role, RoleAssignment, RolePermission
from common.exceptions import DomainError
from common.selectors import tenant_get
from common.services import command, lock_tenant, record, validate_fields


def check_delegation(context, role):
    codes = set(role.permissions.values_list("code", flat=True))
    if not codes <= context.permissions:
        raise DomainError(
            "ROLE_ESCALATION_DENIED", "Cannot delegate permissions you do not hold.", 403
        )
    if (
        role.kind == "OWNER"
        and not RoleAssignment.objects.filter(
            member_id=context.member_id, organization_id=context.organization_id, role__kind="OWNER"
        ).exists()
    ):
        raise DomainError("OWNER_ASSIGNMENT_DENIED", "Only an owner may delegate ownership.", 403)


@command
def assign_role(context, member_id, role_id, *, remove=False):
    lock_tenant(context, "role.manage")
    member = tenant_get(Member, context, member_id, lock=True)
    role = tenant_get(Role, context, role_id)
    check_delegation(context, role)
    if member.status in {"REMOVED", "LEFT"}:
        raise DomainError("RESOURCE_TERMINAL", "Roles cannot be assigned to a departed member.")
    if remove:
        if role.kind == "OWNER":
            protect_last_owner(member)
        changed, _ = RoleAssignment.objects.filter(
            organization_id=context.organization_id, member=member, role=role
        ).delete()
    else:
        _, changed = RoleAssignment.objects.get_or_create(
            organization_id=context.organization_id, member=member, role=role
        )
    if changed:
        record(context, member, "member", "role_changed", ["roles"])
    return member


@command
def create_custom_role(context, name, permission_codes):
    lock_tenant(context, "role.manage")
    codes = set(permission_codes)
    if not codes <= context.permissions:
        raise DomainError(
            "ROLE_ESCALATION_DENIED", "Cannot delegate permissions you do not hold.", 403
        )
    permissions = list(Permission.objects.filter(code__in=codes))
    if len(permissions) != len(codes):
        raise DomainError("INVALID_PERMISSION", "Unknown permission code.", 400)
    role = Role(organization_id=context.organization_id, name=name, kind="CUSTOM")
    validate_fields(role)
    role.save()
    RolePermission.objects.bulk_create(
        [
            RolePermission(
                organization_id=context.organization_id, role=role, permission=permission
            )
            for permission in permissions
        ]
    )
    record(context, role, "role", "created", ["name", "permissions"])
    return role
