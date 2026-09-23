from django.contrib import admin

from apps.branches.models import Branch, BranchMembership
from common.admin import OperatorReadOnlyAdmin


@admin.register(Branch)
class BranchAdmin(OperatorReadOnlyAdmin):
    list_display = ("name", "code", "organization", "status")
    search_fields = ("name", "code", "organization__name")
    list_filter = ("status", "country")


@admin.register(BranchMembership)
class BranchMembershipAdmin(OperatorReadOnlyAdmin):
    list_display = ("id", "organization", "branch", "member", "is_primary", "left_at")
    search_fields = ("member__display_name", "branch__name", "organization__name")
    list_filter = ("is_primary",)
