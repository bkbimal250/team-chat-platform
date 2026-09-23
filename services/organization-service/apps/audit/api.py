from rest_framework import mixins

from apps.audit.models import AuditLog
from common.api import TenantViewSet
from common.serializers import AuditSerializer


class AuditViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, TenantViewSet):
    model = AuditLog
    aggregate = "audit"
    serializer_class = AuditSerializer
    filterset_fields = ["action", "resource_type"]
