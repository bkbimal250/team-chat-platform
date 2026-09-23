from django.db import models
from django.utils import timezone

from common.ids import new_id


class OutboxEvent(models.Model):
    class Status(models.TextChoices):
        PENDING = "PENDING"
        PROCESSING = "PROCESSING"
        PUBLISHED = "PUBLISHED"
        FAILED = "FAILED"

    id = models.UUIDField(primary_key=True, default=new_id, editable=False)
    event_id = models.UUIDField(default=new_id, unique=True)
    event_type = models.CharField(max_length=100)
    event_version = models.PositiveSmallIntegerField(default=1)
    aggregate_type = models.CharField(max_length=80)
    aggregate_id = models.UUIDField()
    organization_id = models.UUIDField(null=True)
    correlation_id = models.CharField(max_length=128)
    payload = models.JSONField()
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    retry_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    available_at = models.DateTimeField(default=timezone.now)
    published_at = models.DateTimeField(null=True)
    last_error = models.CharField(max_length=200, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["status", "available_at"]),
        ]
