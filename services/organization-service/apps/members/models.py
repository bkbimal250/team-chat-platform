from django.db import models
from django.db.models import Q

from common.models import TenantEntity


class Member(TenantEntity):
    class Status(models.TextChoices):
        INVITED = "INVITED"
        ACTIVE = "ACTIVE"
        SUSPENDED = "SUSPENDED"
        LEFT = "LEFT"
        REMOVED = "REMOVED"

    user_id = models.UUIDField(null=True, blank=True)
    display_name = models.CharField(max_length=200)
    employee_code = models.CharField(max_length=50, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)
    department = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status, default=Status.INVITED)
    joined_at = models.DateTimeField(null=True, blank=True)
    suspended_at = models.DateTimeField(null=True, blank=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta(TenantEntity.Meta):
        constraints = TenantEntity.Meta.constraints + [
            models.UniqueConstraint(
                fields=["organization", "user_id"],
                condition=Q(user_id__isnull=False),
                name="member_tenant_user",
            ),
            models.UniqueConstraint(
                fields=["organization", "employee_code"],
                condition=Q(employee_code__isnull=False),
                name="member_tenant_employee",
            ),
        ]
        indexes = [models.Index(fields=["organization", "status"])]
