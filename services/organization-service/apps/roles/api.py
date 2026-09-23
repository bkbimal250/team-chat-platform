from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.response import Response

from apps.roles.models import Permission, Role, RoleAssignment
from apps.roles.services import create_custom_role
from common.api import TenantViewSet
from common.serializers import (
    CustomRoleInput,
    PermissionSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
)


class RoleViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, TenantViewSet):
    model = Role
    aggregate = "role"
    serializer_class = RoleSerializer
    permission_actions = {"create": "role.manage"}

    @extend_schema(request=CustomRoleInput, responses=RoleSerializer)
    def create(self, request):
        serializer = CustomRoleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = create_custom_role(self.context, **serializer.validated_data)
        return Response(self.get_serializer(role).data, status=201)


class PermissionViewSet(mixins.ListModelMixin, TenantViewSet):
    model = Permission
    aggregate = "role"
    serializer_class = PermissionSerializer

    def get_queryset(self):
        return Permission.objects.all()


class RoleAssignmentViewSet(mixins.ListModelMixin, TenantViewSet):
    model = RoleAssignment
    aggregate = "role"
    serializer_class = RoleAssignmentSerializer
    filterset_fields = ["member", "role"]
