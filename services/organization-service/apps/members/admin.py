from django.contrib import admin

from apps.members.models import Member
from common.admin import OperatorReadOnlyAdmin


@admin.register(Member)
class MemberAdmin(OperatorReadOnlyAdmin):
    list_display = ("display_name", "organization", "employee_code", "status", "user_id")
    search_fields = ("display_name", "employee_code", "organization__name")
    list_filter = ("status",)
