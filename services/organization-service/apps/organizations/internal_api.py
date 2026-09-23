import hmac
from uuid import UUID

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.members.models import Member
from apps.organizations.models import Organization


@require_GET
def identity_memberships(request, identity_id: UUID):
    """Versioned internal contract used by identity-service only; never expose it through a gateway."""
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse(
            {
                "error": {
                    "code": "SERVICE_UNAUTHORIZED",
                    "message": "Unauthorized service identity.",
                    "details": {},
                    "correlation_id": getattr(request, "correlation_id", ""),
                }
            },
            status=401,
        )
    rows = Member.objects.filter(
        user_id=identity_id,
        status=Member.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).values("organization_id", "id", "status")
    return JsonResponse(
        {
            "contract_version": "identity-memberships.v1",
            "memberships": [
                {
                    "organization_id": str(row["organization_id"]),
                    "member_id": str(row["id"]),
                    "status": row["status"],
                }
                for row in rows
            ],
        }
    )
