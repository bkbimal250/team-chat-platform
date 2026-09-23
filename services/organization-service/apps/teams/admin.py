from django.contrib import admin

from apps.teams.models import Team, TeamMembership
from common.admin import OperatorReadOnlyAdmin


@admin.register(Team)
class TeamAdmin(OperatorReadOnlyAdmin):
    list_display = ("name", "organization", "branch", "status")
    search_fields = ("name", "organization__name")
    list_filter = ("status", "type")


@admin.register(TeamMembership)
class TeamMembershipAdmin(OperatorReadOnlyAdmin):
    list_display = ("id", "organization", "team", "member", "role", "status")
    search_fields = ("member__display_name", "team__name", "organization__name")
    list_filter = ("role", "status")
