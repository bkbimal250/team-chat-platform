from django.db.models import Q
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import mixins
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.invitations.models import Invitation
from apps.invitations.services import (
    accept_invitation,
    create_invitation,
    resend_invitation,
    revoke_invitation,
)
from common.api import TenantViewSet
from common.serializers import AcceptInvitationInput, InvitationSerializer


class InvitationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, TenantViewSet):
    model = Invitation
    aggregate = "invitation"
    serializer_class = InvitationSerializer
    filterset_fields = []

    def get_queryset(self):
        rows = super().get_queryset()
        status = self.request.query_params.get("status")
        if status == "EXPIRED":
            return rows.filter(
                Q(status="EXPIRED") | Q(status="PENDING", expires_at__lte=timezone.now())
            )
        if status == "PENDING":
            return rows.filter(status="PENDING", expires_at__gt=timezone.now())
        return rows.filter(status=status) if status else rows

    permission_actions = {
        "create": "invitation.create",
        "revoke": "invitation.revoke",
        "accept": "invitation.accept",
        "resend": "invitation.create",
    }

    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(self.context, serializer.validated_data)
        result = self.get_serializer(invitation).data
        if getattr(invitation, "development_url", None):
            result["development_url"] = invitation.development_url
        return Response(result, status=201)

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

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        invitation = resend_invitation(self.context, self.get_object().id)
        return Response(
            {**self.get_serializer(invitation).data, "development_url": invitation.development_url}
        )
