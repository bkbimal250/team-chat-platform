from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.members.filters import MemberFilter
from apps.members.models import Member
from apps.roles.services import assign_role
from common.api import ResourceViewSet
from common.serializers import MemberSerializer, RoleAssignmentInput


class MemberViewSet(ResourceViewSet):
    model = Member
    aggregate = "member"
    serializer_class = MemberSerializer
    filterset_class = MemberFilter
    search_fields = ["display_name", "employee_code"]
    permission_actions = {"roles": "role.manage"}

    @extend_schema(request=RoleAssignmentInput, responses=MemberSerializer)
    @action(detail=True, methods=["post"])
    def roles(self, request, pk=None):
        member = self.get_object()
        serializer = RoleAssignmentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = assign_role(self.context, member.id, **serializer.validated_data)
        return Response(self.get_serializer(member).data)
