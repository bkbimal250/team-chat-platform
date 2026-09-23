from django.contrib import admin

from apps.organizations.models import Organization, OrganizationSettings
from common.admin import OperatorReadOnlyAdmin


@admin.register(Organization)
class OrganizationAdmin(OperatorReadOnlyAdmin):
    list_display = ("name", "slug", "status", "created_at")
    list_filter = ("status", "organization_type")
    search_fields = ("name", "slug", "id")


@admin.register(OrganizationSettings)
class SettingsAdmin(OperatorReadOnlyAdmin):
    list_display = ("organization", "allow_member_invites", "max_members", "max_teams")
    search_fields = ("organization__name",)
    list_filter = ("allow_member_invites",)
