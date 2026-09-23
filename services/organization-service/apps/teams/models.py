from django.db import models
from django.db.models import Q
from django.utils import timezone

from common.models import ResourceStatus, TenantEntity


class Team(TenantEntity):
    class Type(models.TextChoices):
        STANDARD = "STANDARD"
        DEPARTMENT = "DEPARTMENT"
        PROJECT = "PROJECT"

    branch = models.ForeignKey("branches.Branch", on_delete=models.PROTECT, null=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=Type, default=Type.STANDARD)
    status = models.CharField(max_length=20, choices=ResourceStatus, default=ResourceStatus.ACTIVE)
    created_by_member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, null=True, blank=True
    )

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(fields=["organization", "name"], name="team_tenant_name")
        ]
        indexes = [
            models.Index(fields=["organization", "branch"]),
            models.Index(fields=["organization", "status"]),
        ]


class TeamMembership(TenantEntity):
    class Role(models.TextChoices):
        OWNER = "OWNER"
        ADMIN = "ADMIN"
        MEMBER = "MEMBER"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE"
        LEFT = "LEFT"

    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="team_memberships"
    )
    role = models.CharField(max_length=20, choices=Role, default=Role.MEMBER)
    status = models.CharField(max_length=20, choices=Status, default=Status.ACTIVE)
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(
                fields=["team", "member"],
                condition=Q(status="ACTIVE"),
                name="team_active_membership",
            ),
            models.CheckConstraint(
                condition=Q(status="ACTIVE", left_at__isnull=True)
                | Q(status="LEFT", left_at__isnull=False),
                name="team_membership_dates",
            ),
        ]
        indexes = [models.Index(fields=["organization", "member"])]
