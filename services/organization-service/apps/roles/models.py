from django.db import models

from common.models import Entity, TenantEntity


class Permission(Entity):
    code = models.CharField(max_length=80, unique=True)
    description = models.CharField(max_length=200)


class Role(TenantEntity):
    class Kind(models.TextChoices):
        OWNER = "OWNER"
        ADMIN = "ADMIN"
        MANAGER = "MANAGER"
        MEMBER = "MEMBER"
        CUSTOM = "CUSTOM"

    name = models.CharField(max_length=80)
    kind = models.CharField(max_length=20, choices=Kind, default=Kind.CUSTOM)
    permissions = models.ManyToManyField(Permission, through="RolePermission")

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(fields=["organization", "name"], name="role_tenant_name")
        ]


class RolePermission(TenantEntity):
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(fields=["role", "permission"], name="role_permission_unique")
        ]


class RoleAssignment(TenantEntity):
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="role_assignments"
    )
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(fields=["member", "role"], name="role_assignment_unique")
        ]
        indexes = [models.Index(fields=["organization", "member"])]
