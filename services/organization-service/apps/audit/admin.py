from django.contrib import admin

from apps.audit.models import AuditLog
from common.admin import OperatorReadOnlyAdmin


@admin.register(AuditLog)
class AuditAdmin(OperatorReadOnlyAdmin):
    list_display = ("created_at", "organization", "action", "resource_type", "correlation_id")
    search_fields = ("correlation_id", "resource_id", "organization__name")
    list_filter = ("action", "resource_type")
