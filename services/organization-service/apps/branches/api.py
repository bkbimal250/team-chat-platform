from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.branches.models import Branch, BranchMembership
from apps.teams.api import MembershipActions
from apps.teams.services import set_primary_branch
from common.api import ResourceViewSet
from common.selectors import tenant_get
from common.serializers import BranchMembershipInput, BranchMembershipSerializer, BranchSerializer


class BranchViewSet(MembershipActions, ResourceViewSet):
    model = Branch
    aggregate = "branch"
    serializer_class = BranchSerializer
    filterset_fields = ["status", "city"]
    search_fields = ["name", "code"]
    branch_membership = True
    membership_model = BranchMembership
    membership_serializer = BranchMembershipSerializer
    membership_input = BranchMembershipInput

    @extend_schema(request=BranchMembershipInput, responses=BranchMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        return super().members(request, pk)

    @extend_schema(request=None, responses=BranchMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/leave"
    )
    def remove_member(self, request, pk=None, membership_id=None):
        return super().remove_member(request, pk, membership_id)

    @extend_schema(request=None, responses=BranchMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/primary"
    )
    def primary(self, request, pk=None, membership_id=None):
        parent = self.get_object()
        membership = tenant_get(BranchMembership, self.context, membership_id)
        if membership.branch_id != parent.id:
            from django.http import Http404

            raise Http404
        result = set_primary_branch(self.context, membership.id)
        return Response(BranchMembershipSerializer(result).data)
