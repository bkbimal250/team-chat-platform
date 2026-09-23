from django.db import models
from django.db.models import Q
from django.utils import timezone

from common.models import ResourceStatus, TenantEntity


class Branch(TenantEntity):
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=32, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=2)
    postal_code = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, choices=ResourceStatus, default=ResourceStatus.ACTIVE)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(fields=["organization", "code"], name="branch_tenant_code")
        ]
        indexes = [models.Index(fields=["organization", "status"])]


class BranchMembership(TenantEntity):
    branch = models.ForeignKey(Branch, on_delete=models.PROTECT)
    member = models.ForeignKey(
        "members.Member", on_delete=models.PROTECT, related_name="branch_memberships"
    )
    is_primary = models.BooleanField(default=False)
    joined_at = models.DateTimeField(default=timezone.now)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(
                fields=["branch", "member"],
                condition=Q(left_at__isnull=True),
                name="branch_active_membership",
            ),
            models.UniqueConstraint(
                fields=["organization", "member"],
                condition=Q(is_primary=True, left_at__isnull=True),
                name="member_one_primary_branch",
            ),
            models.CheckConstraint(
                condition=Q(is_primary=False) | Q(left_at__isnull=True),
                name="primary_branch_is_current",
            ),
        ]
        indexes = [models.Index(fields=["organization", "member"])]
