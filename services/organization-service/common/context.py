from dataclasses import dataclass, field
from uuid import UUID

from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from common.ids import new_id


@dataclass(frozen=True)
class TenantContext:
    organization_id: UUID
    member_id: UUID | None
    user_id: UUID | None = None
    permissions: frozenset[str] = field(default_factory=frozenset)
    correlation_id: str = field(default_factory=lambda: str(new_id()))
    ip_address: str | None = None
    user_agent: str = ""


class DevelopmentContextAuthentication(BaseAuthentication):
    """UNSAFE local adapter. Never enabled in production; DB roles are authoritative."""

    def authenticate(self, request):
        if not settings.DEV_CONTEXT_ENABLED:
            return None
        member_id = request.headers.get("X-Dev-Member-ID")
        if not member_id:
            return None
        from apps.members.models import Member
        from common.authorization import effective_permissions

        try:
            member = Member.objects.select_related("organization").get(
                id=UUID(member_id), status="ACTIVE", organization__status="ACTIVE"
            )
        except (ValueError, Member.DoesNotExist):
            raise AuthenticationFailed("Invalid development member context.") from None
        context = TenantContext(
            member.organization_id,
            member.id,
            member.user_id,
            effective_permissions(member),
            request.correlation_id,
            request.META.get("REMOTE_ADDR"),
            request.headers.get("User-Agent", "")[:512],
        )
        request.tenant_context = context
        request._request.tenant_context = context
        return (None, context)

    def authenticate_header(self, request):
        return "TenantContext"
