from dataclasses import replace

from django.utils import timezone

from apps.members.models import Member
from apps.organizations.models import Organization, OrganizationSettings
from apps.roles.models import Permission, Role, RoleAssignment, RolePermission
from common.authorization import PERMISSIONS, ROLE_PERMISSIONS
from common.context import TenantContext
from common.exceptions import DomainError
from common.services import command, lock_tenant, record, validate_fields


@command
def provision_organization(
    *, name: str, slug: str, owner_name: str, owner_user_id, correlation_id=None
):
    """Operator-only command; never exposed as an unauthenticated public API."""
    organization = Organization(name=name, slug=slug, display_name=name)
    validate_fields(organization)
    organization.save()
    OrganizationSettings.objects.create(organization=organization)
    permissions = {
        code: Permission.objects.get_or_create(code=code, defaults={"description": code})[0]
        for code in sorted(PERMISSIONS)
    }
    for name, codes in ROLE_PERMISSIONS.items():
        role = Role.objects.create(organization=organization, name=name, kind=name)
        RolePermission.objects.bulk_create(
            [
                RolePermission(organization=organization, role=role, permission=permissions[code])
                for code in codes
            ]
        )
    owner = Member.objects.create(
        organization=organization,
        user_id=owner_user_id,
        display_name=owner_name,
        status="ACTIVE",
        joined_at=timezone.now(),
    )
    RoleAssignment.objects.create(
        organization=organization,
        member=owner,
        role=Role.objects.get(organization=organization, kind="OWNER"),
    )
    context = TenantContext(organization.id, owner.id, owner.user_id, PERMISSIONS)
    if correlation_id:
        context = replace(context, correlation_id=correlation_id)
    record(context, organization, "organization", "created")
    record(context, owner, "member", "created")
    record(context, owner, "member", "activated", ["status"])
    record(context, owner, "member", "role_changed", ["roles"])
    return organization, owner


@command
def update_organization(context, data):
    organization = lock_tenant(context, "organization.update")
    for field, value in data.items():
        setattr(organization, field, value)
    validate_fields(organization)
    organization.save()
    record(context, organization, "organization", "updated", data)
    return organization


@command
def update_settings(context, data):
    organization = lock_tenant(context, "organization.update")
    settings = organization.settings
    for field, value in data.items():
        setattr(settings, field, value)
    validate_fields(settings)
    settings.save()
    record(context, settings, "organization_settings", "updated", data)
    return settings


@command
def set_organization_status(context, status, *, operator=False):
    """Operator path also permits recovery of a suspended tenant."""
    organization = (
        Organization.objects.select_for_update().get(id=context.organization_id)
        if operator
        else lock_tenant(context, "organization.update")
    )
    allowed = {
        "ACTIVE": {"SUSPENDED", "DISABLED"},
        "SUSPENDED": {"ACTIVE", "DISABLED"},
        "DISABLED": {"ACTIVE", "DELETED"},
    }
    if status not in allowed.get(organization.status, set()):
        raise DomainError("INVALID_TRANSITION", "This lifecycle transition is not allowed.")
    organization.status = status
    organization.suspended_at = timezone.now() if status == "SUSPENDED" else None
    organization.deleted_at = timezone.now() if status == "DELETED" else None
    organization.save()
    record(
        context,
        organization,
        "organization",
        {
            "ACTIVE": "updated",
            "SUSPENDED": "suspended",
            "DISABLED": "disabled",
            "DELETED": "deleted",
        }[status],
        ["status"],
    )
    return organization
