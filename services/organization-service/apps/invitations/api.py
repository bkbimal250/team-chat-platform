from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.invitations.models import Invitation
from apps.invitations.services import accept_invitation, create_invitation, revoke_invitation
from common.api import TenantViewSet
from common.serializers import AcceptInvitationInput, InvitationSerializer


class InvitationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, TenantViewSet):
    model = Invitation
    aggregate = "invitation"
    serializer_class = InvitationSerializer
    filterset_fields = ["status"]
    permission_actions = {
        "create": "invitation.create",
        "revoke": "invitation.revoke",
        "accept": "invitation.accept",
    }

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(self.context, serializer.validated_data)
        return Response(self.get_serializer(invitation).data, status=201)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        invitation = revoke_invitation(self.context, self.get_object().id)
        return Response(self.get_serializer(invitation).data)

    @extend_schema(request=AcceptInvitationInput)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        serializer = AcceptInvitationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = accept_invitation(
            self.context, self.get_object().id, **serializer.validated_data
        )
        return Response(self.get_serializer(invitation).data)
