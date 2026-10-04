import hmac
import json
from uuid import UUID

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import connection, transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from apps.members.models import Member
from apps.organizations.models import Organization
from apps.organizations.services import provision_organization
from common.exceptions import DomainError


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


@require_POST
@csrf_exempt
def company_registration(request):
    """Authenticated Identity saga only. The organization ID is its idempotency key."""
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        data = json.loads(request.body)
        if set(data) != {"organization_id", "identity_id", "company_name", "owner_name", "email"}:
            raise ValueError()
        organization_id, identity_id = UUID(data["organization_id"]), UUID(data["identity_id"])
        with transaction.atomic():
            # Serialize retries even before the organization exists.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)", [organization_id.int % (2**63 - 1)]
                )
            existing = Organization.objects.filter(id=organization_id).first()
            if existing:
                owner = Member.objects.get(organization=existing, user_id=identity_id)
            else:
                existing, owner = provision_organization(
                    name=data["company_name"],
                    slug="company-" + organization_id.hex,
                    owner_name=data["owner_name"],
                    owner_user_id=identity_id,
                    organization_id=organization_id,
                    email=data["email"],
                    correlation_id=getattr(request, "correlation_id", ""),
                )
        return JsonResponse({"organization_id": str(existing.id), "member_id": str(owner.id)})
    except (ValueError, TypeError, KeyError, Member.DoesNotExist, ValidationError, DomainError):
        return JsonResponse({"error": {"code": "PROVISIONING_CONFLICT"}}, status=409)
