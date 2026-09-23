from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organizations.models import Organization
from apps.organizations.services import (
    set_organization_status,
    update_organization,
    update_settings,
)
from common.api import TenantViewSet
from common.serializers import LifecycleInput, OrganizationSerializer, SettingsSerializer


class OrganizationViewSet(TenantViewSet):
    model = Organization
    aggregate = "organization"
    serializer_class = OrganizationSerializer

    def required_permission(self):
        return (
            "organization.view"
            if self.request.method in {"GET", "HEAD", "OPTIONS"}
            else "organization.update"
        )

    @action(detail=False, methods=["get", "patch"])
    def current(self, request):
        organization = Organization.objects.get(id=self.context.organization_id)
        if request.method == "PATCH":
            serializer = self.get_serializer(organization, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            organization = update_organization(self.context, serializer.validated_data)
        return Response(self.get_serializer(organization).data)

    @extend_schema(request=SettingsSerializer, responses=SettingsSerializer)
    @action(detail=False, methods=["get", "patch"], url_path="current/settings")
    def organization_settings(self, request):
        settings = Organization.objects.get(id=self.context.organization_id).settings
        if request.method == "PATCH":
            serializer = SettingsSerializer(settings, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            settings = update_settings(self.context, serializer.validated_data)
        return Response(SettingsSerializer(settings).data)

    @extend_schema(request=LifecycleInput)
    @action(detail=False, methods=["post"], url_path="current/lifecycle")
    def lifecycle(self, request):
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = set_organization_status(self.context, serializer.validated_data["status"])
        return Response(self.get_serializer(organization).data)
