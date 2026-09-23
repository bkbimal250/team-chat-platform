from rest_framework.permissions import BasePermission

from common.exceptions import DomainError

PERMISSIONS = frozenset(
    {
        "organization.view",
        "organization.update",
        "member.view",
        "member.create",
        "member.update",
        "member.remove",
        "team.view",
        "team.create",
        "team.update",
        "team.delete",
        "branch.view",
        "branch.create",
        "branch.update",
        "branch.delete",
        "invitation.view",
        "invitation.create",
        "invitation.revoke",
        "invitation.accept",
        "device.view",
        "device.revoke",
        "audit.view",
        "billing.view",
        "billing.manage",
        "role.view",
        "role.manage",
    }
)
ROLE_PERMISSIONS = {
    "OWNER": PERMISSIONS,
    "ADMIN": PERMISSIONS - {"billing.manage", "role.manage", "invitation.accept"},
    "MANAGER": frozenset(
        {
            "organization.view",
            "member.view",
            "team.view",
            "team.create",
            "team.update",
            "branch.view",
            "invitation.view",
            "invitation.create",
            "role.view",
        }
    ),
    "MEMBER": frozenset(
        {"organization.view", "member.view", "team.view", "branch.view", "role.view"}
    ),
}


def effective_permissions(member) -> frozenset[str]:
    from apps.roles.models import Permission

    return frozenset(
        Permission.objects.filter(
            role__roleassignment__member=member, role__organization_id=member.organization_id
        ).values_list("code", flat=True)
    )


def require(context, permission: str) -> None:
    if context is None or permission not in context.permissions:
        raise DomainError("PERMISSION_DENIED", "Permission denied.", 403)


class TenantPermission(BasePermission):
    def has_permission(self, request, view):
        context = getattr(request, "tenant_context", None)
        if context is None:
            return False
        permission = view.required_permission()
        return permission in context.permissions
