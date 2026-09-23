import django_filters

from apps.members.models import Member


class MemberFilter(django_filters.FilterSet):
    team = django_filters.UUIDFilter(method="by_team")
    branch = django_filters.UUIDFilter(method="by_branch")
    role = django_filters.UUIDFilter(field_name="role_assignments__role_id", distinct=True)

    def by_team(self, queryset, name, value):
        return queryset.filter(
            team_memberships__team_id=value, team_memberships__status="ACTIVE"
        ).distinct()

    def by_branch(self, queryset, name, value):
        return queryset.filter(
            branch_memberships__branch_id=value, branch_memberships__left_at__isnull=True
        ).distinct()

    class Meta:
        model = Member
        fields = ["status", "team", "branch", "role"]
