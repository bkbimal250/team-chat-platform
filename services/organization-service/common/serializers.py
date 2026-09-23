from rest_framework import serializers

from apps.audit.models import AuditLog
from apps.branches.models import Branch, BranchMembership
from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.organizations.models import Organization, OrganizationSettings
from apps.roles.models import Permission, Role, RoleAssignment
from apps.teams.models import Team, TeamMembership


class StrictSerializer(serializers.ModelSerializer):
    """Reject unknown/read-only input rather than silently accepting tenant/identity spoofing."""

    def to_internal_value(self, data):
        forbidden = set(data) - {name for name, field in self.fields.items() if not field.read_only}
        if forbidden:
            raise serializers.ValidationError(
                {name: "Unknown or read-only field." for name in sorted(forbidden)}
            )
        return super().to_internal_value(data)

    class Meta:
        fields = "__all__"
        read_only_fields = ("id", "organization", "created_at", "updated_at", "status")
        validators = []


class OrganizationSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = Organization
        read_only_fields = StrictSerializer.Meta.read_only_fields + ("suspended_at", "deleted_at")


class SettingsSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = OrganizationSettings


class BranchSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = Branch


class TeamSerializer(StrictSerializer):
    branch_id = serializers.UUIDField(required=False, allow_null=True)

    class Meta(StrictSerializer.Meta):
        model = Team
        exclude = ("branch",)
        fields = None
        read_only_fields = StrictSerializer.Meta.read_only_fields + ("created_by_member",)


class MemberSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = Member
        read_only_fields = StrictSerializer.Meta.read_only_fields + (
            "joined_at",
            "suspended_at",
            "left_at",
            "user_id",
        )


class InvitationSerializer(StrictSerializer):
    team_id = serializers.UUIDField(required=False, allow_null=True)
    branch_id = serializers.UUIDField(required=False, allow_null=True)
    intended_role_id = serializers.UUIDField()

    class Meta(StrictSerializer.Meta):
        model = Invitation
        exclude = ("team", "branch", "intended_role")
        fields = None
        read_only_fields = StrictSerializer.Meta.read_only_fields + (
            "accepted_at",
            "revoked_at",
            "accepted_member",
            "invited_by_member",
        )


class TeamMembershipSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = TeamMembership


class BranchMembershipSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = BranchMembership


class PermissionSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = Permission


class RoleSerializer(StrictSerializer):
    permissions = serializers.SlugRelatedField(slug_field="code", read_only=True, many=True)

    class Meta(StrictSerializer.Meta):
        model = Role


class RoleAssignmentSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = RoleAssignment


class AuditSerializer(StrictSerializer):
    class Meta(StrictSerializer.Meta):
        model = AuditLog


class StrictInputSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({name: "Unknown field." for name in sorted(unknown)})
        return super().to_internal_value(data)


class TeamMembershipInput(StrictInputSerializer):
    member_id = serializers.UUIDField()
    role = serializers.ChoiceField(choices=TeamMembership.Role, default="MEMBER")


class BranchMembershipInput(StrictInputSerializer):
    member_id = serializers.UUIDField()
    is_primary = serializers.BooleanField(default=False)


class LifecycleInput(StrictInputSerializer):
    status = serializers.CharField(max_length=20)


class RoleAssignmentInput(StrictInputSerializer):
    role_id = serializers.UUIDField()
    remove = serializers.BooleanField(default=False)


class CustomRoleInput(StrictInputSerializer):
    name = serializers.CharField(max_length=80)
    permission_codes = serializers.ListField(
        child=serializers.CharField(max_length=80), max_length=100
    )


class AcceptInvitationInput(StrictInputSerializer):
    member_id = serializers.UUIDField()
