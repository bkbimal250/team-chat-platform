from django.contrib import admin

from apps.roles.models import Permission, Role, RoleAssignment, RolePermission
from common.admin import OperatorReadOnlyAdmin


@admin.register(Role)
class RoleAdmin(OperatorReadOnlyAdmin):
    list_display = ("name", "organization", "kind")
    search_fields = ("name", "organization__name")
    list_filter = ("kind",)


@admin.register(Permission)
class PermissionAdmin(OperatorReadOnlyAdmin):
    list_display = ("code", "description")
    search_fields = ("code",)


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(OperatorReadOnlyAdmin):
    list_display = ("id", "organization", "member", "role")
    search_fields = ("member__display_name", "role__name", "organization__name")


@admin.register(RolePermission)
class RolePermissionAdmin(OperatorReadOnlyAdmin):
    list_display = ("organization", "role", "permission")
    search_fields = ("role__name", "permission__code")
