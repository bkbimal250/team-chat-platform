from django.contrib import admin

from apps.invitations.models import Invitation
from common.admin import OperatorReadOnlyAdmin


@admin.register(Invitation)
class InvitationAdmin(OperatorReadOnlyAdmin):
    list_display = ("id", "organization", "intended_role", "status", "expires_at")
    search_fields = ("id", "organization__name")
    list_filter = ("status",)
