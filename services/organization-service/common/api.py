from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from common.selectors import tenant_queryset
from common.serializers import LifecycleInput
from common.services import create_resource, transition, update_resource


class TenantViewSet(viewsets.GenericViewSet):
    http_method_names = ["get", "post", "patch", "head", "options"]
    permission_actions = {}

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return self.model.objects.none()
        return tenant_queryset(self.model, self.request.tenant_context)

    def required_permission(self):
        return self.permission_actions.get(self.action, f"{self.aggregate}.view")

    @property
    def context(self):
        return self.request.tenant_context


class ResourceViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, TenantViewSet):
    def required_permission(self):
        if self.action == "create":
            return f"{self.aggregate}.create"
        if self.action in {"partial_update", "lifecycle"}:
            return f"{self.aggregate}.update"
        return super().required_permission()

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = create_resource(
            self.context, self.model, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = update_resource(
            self.context, self.model, instance.id, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data)

    @extend_schema(request=LifecycleInput)
    @action(detail=True, methods=["post"])
    def lifecycle(self, request, pk=None):
        instance = self.get_object()
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = transition(
            self.context,
            self.model,
            instance.id,
            serializer.validated_data["status"],
            self.aggregate,
        )
        return Response(self.get_serializer(result).data)
