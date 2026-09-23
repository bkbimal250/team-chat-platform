from uuid import UUID

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.teams.models import Team, TeamMembership
from apps.teams.services import add_membership, end_membership
from common.api import ResourceViewSet
from common.selectors import tenant_queryset
from common.serializers import TeamMembershipInput, TeamMembershipSerializer, TeamSerializer


class MembershipActions:
    branch_membership = False
    membership_model = TeamMembership
    membership_serializer = TeamMembershipSerializer
    membership_input = TeamMembershipInput

    def required_permission(self):
        if self.action in {"members", "remove_member", "primary"}:
            return (
                f"{self.aggregate}.view"
                if self.request.method in {"GET", "HEAD", "OPTIONS"}
                else f"{self.aggregate}.update"
            )
        return super().required_permission()

    @extend_schema(request=TeamMembershipInput, responses=TeamMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        parent = self.get_object()
        if request.method == "POST":
            serializer = self.membership_input(data=request.data)
            serializer.is_valid(raise_exception=True)
            membership = add_membership(
                self.context, parent.id, branch=self.branch_membership, **serializer.validated_data
            )
            return Response(self.membership_serializer(membership).data, status=201)
        queryset = tenant_queryset(self.membership_model, self.context).filter(
            **{self.aggregate: parent}
        )
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.membership_serializer(page, many=True).data)

    @extend_schema(request=None, responses=TeamMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/leave"
    )
    def remove_member(self, request, pk=None, membership_id=None):
        parent = self.get_object()
        membership = end_membership(
            self.context, parent.id, UUID(membership_id), branch=self.branch_membership
        )
        return Response(self.membership_serializer(membership).data)


class TeamViewSet(MembershipActions, ResourceViewSet):
    model = Team
    aggregate = "team"
    serializer_class = TeamSerializer
    filterset_fields = ["branch", "status"]
    search_fields = ["name"]
