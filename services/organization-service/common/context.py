from dataclasses import dataclass, field
from uuid import UUID

import jwt
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


def _context_from_member(request, organization_id: UUID, member_id: UUID, identity_id: UUID):
    from apps.members.models import Member
    from common.authorization import effective_permissions

    try:
        member = Member.objects.select_related("organization").get(
            id=member_id,
            organization_id=organization_id,
            user_id=identity_id,
            status="ACTIVE",
            organization__status="ACTIVE",
        )
    except Member.DoesNotExist as exc:
        raise AuthenticationFailed("Invalid tenant membership.") from exc
    context = TenantContext(
        member.organization_id,
        member.id,
        member.user_id,
        effective_permissions(member),
        request.headers.get("X-Correlation-ID", str(new_id())),
        request.META.get("REMOTE_ADDR"),
        request.headers.get("User-Agent", "")[:512],
    )
    request.tenant_context = context
    request._request.tenant_context = context
    return context


class JWTContextAuthentication(BaseAuthentication):
    """Production access-token verification for Organization requests."""

    def authenticate(self, request):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        if not settings.JWT_PUBLIC_KEY:
            raise AuthenticationFailed("JWT verification is not configured.")
        try:
            claims = jwt.decode(
                header.removeprefix("Bearer ").strip(),
                settings.JWT_PUBLIC_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
                options={"require": ["sub", "org", "mid", "exp"]},
            )
            context = _context_from_member(
                request, UUID(claims["org"]), UUID(claims["mid"]), UUID(claims["sub"])
            )
        except (jwt.PyJWTError, KeyError, ValueError) as exc:
            raise AuthenticationFailed("Invalid access token.") from exc
        return (None, context)

    def authenticate_header(self, request):
        return "Bearer"


class DevelopmentContextAuthentication(BaseAuthentication):
    """Local-only adapter; production always uses JWTContextAuthentication."""

    def authenticate(self, request):
        if not settings.DEV_CONTEXT_ENABLED:
            return None
        member_id = request.headers.get("X-Dev-Member-ID")
        if not member_id:
            return None
        from apps.members.models import Member

        try:
            member = Member.objects.select_related("organization").get(
                id=UUID(member_id), status="ACTIVE", organization__status="ACTIVE"
            )
        except (ValueError, Member.DoesNotExist):
            raise AuthenticationFailed("Invalid development member context.") from None
        return (
            None,
            _context_from_member(request, member.organization_id, member.id, member.user_id),
        )

    def authenticate_header(self, request):
        return "TenantContext"
