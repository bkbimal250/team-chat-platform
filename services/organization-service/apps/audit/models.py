from django.db import models

from common.ids import new_id
from common.models import TenantQuerySet


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=new_id, editable=False)
    organization = models.ForeignKey(
        "organizations.Organization", on_delete=models.PROTECT, null=True
    )
    actor_user_id = models.UUIDField(null=True)
    actor_member = models.ForeignKey("members.Member", on_delete=models.PROTECT, null=True)
    action = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=80)
    resource_id = models.UUIDField()
    metadata = models.JSONField(default=dict)
    ip_address = models.GenericIPAddressField(null=True)
    user_agent = models.CharField(max_length=512, blank=True)
    correlation_id = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["organization", "created_at"]),
            models.Index(fields=["actor_member", "created_at"]),
        ]
