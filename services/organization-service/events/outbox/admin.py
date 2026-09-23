from django.contrib import admin

from common.admin import OperatorReadOnlyAdmin
from events.outbox.models import OutboxEvent


@admin.register(OutboxEvent)
class OutboxAdmin(OperatorReadOnlyAdmin):
    list_display = (
        "event_id",
        "organization_id",
        "event_type",
        "status",
        "retry_count",
        "created_at",
    )
    search_fields = ("event_id", "organization_id", "correlation_id")
    list_filter = ("status", "event_type")
