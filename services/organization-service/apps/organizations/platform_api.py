"""Read-only platform structure. Persistent authority checked by Identity each request."""

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.db.models import Count
from django.http import JsonResponse
from django.views.decorators.http import require_GET

from apps.branches.models import Branch
from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.organizations.models import Organization
from apps.roles.models import RoleAssignment
from apps.teams.models import Team


def authorize(request):
    token = request.headers.get("Authorization", "")
    if not token.lower().startswith("bearer "):
        return JsonResponse({"detail": "Authentication required"}, status=401)
    base = os.getenv("IDENTITY_SERVICE_URL", "http://127.0.0.1:8001").rstrip("/")
    try:
        with urlopen(Request(base + "/api/v1/platform/me", headers={"Authorization": token}), timeout=3) as response:
            data = json.load(response)
        if "platform.organizations.read" not in data.get("permissions", []):
            return JsonResponse({"detail": "Platform permission required"}, status=403)
    except HTTPError as error:
        return JsonResponse({"detail": "Platform authorization required"}, status=error.code if error.code in {401, 403, 429} else 503)
    except (URLError, ValueError, TimeoutError, OSError):
        return JsonResponse({"detail": "Platform authorization unavailable"}, status=503)
    return None


def metadata(row):
    return {"id": str(row.id), "name": row.name, "display_name": row.display_name, "status": row.status, "created_at": row.created_at.isoformat()}


def pagination(request):
    try:
        limit, offset = int(request.GET.get("limit", 20)), int(request.GET.get("offset", 0))
        if not 1 <= limit <= 100 or not 0 <= offset <= 100000:
            raise ValueError
    except ValueError:
        return None, JsonResponse({"detail": "Invalid pagination"}, status=400)
    return (limit, offset), None


def member_data(member, roles_by_member, *, organization=None):
    result = {
        "id": str(member.id),
        "user_id": str(member.user_id) if member.user_id else None,
        "display_name": member.display_name,
        "status": member.status,
        "joined_at": member.joined_at.isoformat() if member.joined_at else None,
        "created_at": member.created_at.isoformat(),
        "roles": roles_by_member.get(member.id, []),
    }
    if organization is not None:
        result.update(
            {
                "organization_id": str(organization.id),
                "organization_name": organization.name,
                "organization_display_name": organization.display_name,
            }
        )
    return result


def roles_for(query):
    assignments = RoleAssignment.objects.filter(member__in=query).select_related("role")
    grouped = {}
    for assignment in assignments:
        grouped.setdefault(assignment.member_id, []).append(assignment.role.kind)
    return {key: sorted(set(value)) for key, value in grouped.items()}


@require_GET
def organizations(request, organization_id=None):
    denied = authorize(request)
    if denied is not None:
        return denied
    if organization_id:
        row = Organization.objects.filter(id=organization_id).first()
        if row is None:
            return JsonResponse({"detail": "Organization not found"}, status=404)
        result = metadata(row)
        # This bounded overview is intentionally separate from the paginated
        # membership contract below.
        members = Member.objects.filter(organization_id=row.id).order_by("created_at", "id")[:100]
        result["members"] = [member_data(member, roles_for(members)) for member in members]
        result["branches"] = list(Branch.objects.filter(organization_id=row.id).values("id", "name", "status")[:100])
        result["teams"] = list(Team.objects.filter(organization_id=row.id).values("id", "name", "status")[:100])
        result["structure_limit"] = 100
        return JsonResponse(result)
    values, error = pagination(request)
    if error:
        return error
    limit, offset = values
    query = Organization.objects.all()
    search = request.GET.get("search", "")
    if len(search) > 100:
        return JsonResponse({"detail": "Search too long"}, status=400)
    if search:
        query = query.filter(display_name__icontains=search)
    status = request.GET.get("status", "")
    if status:
        if status not in Organization.Status.values:
            return JsonResponse({"detail": "Invalid status"}, status=400)
        query = query.filter(status=status)
    return JsonResponse({"total": query.count(), "items": [metadata(row) for row in query.order_by("created_at", "id")[offset:offset + limit]]})


@require_GET
def memberships(request, organization_id=None, identity_id=None):
    denied = authorize(request)
    if denied is not None:
        return denied
    if organization_id is None and identity_id is None:
        return JsonResponse({"detail": "Membership scope required"}, status=400)
    values, error = pagination(request)
    if error:
        return error
    limit, offset = values
    query = Member.objects.select_related("organization")
    if organization_id is not None:
        organization = Organization.objects.filter(id=organization_id).first()
        if organization is None:
            return JsonResponse({"detail": "Organization not found"}, status=404)
        query = query.filter(organization=organization)
        search = request.GET.get("search", "").strip()
        if len(search) > 100:
            return JsonResponse({"detail": "Search too long"}, status=400)
        if search:
            query = query.filter(display_name__icontains=search)
        status = request.GET.get("status", "")
        if status:
            if status not in Member.Status.values:
                return JsonResponse({"detail": "Invalid status"}, status=400)
            query = query.filter(status=status)
    else:
        query = query.filter(user_id=identity_id)
    total = query.count()
    rows = list(query.order_by("created_at", "id")[offset : offset + limit])
    roles = roles_for(rows)
    return JsonResponse(
        {
            "total": total,
            "items": [member_data(member, roles, organization=member.organization) for member in rows],
        }
    )


@require_GET
def owners(request, organization_id):
    denied = authorize(request)
    if denied is not None:
        return denied
    organization = Organization.objects.filter(id=organization_id).first()
    if organization is None:
        return JsonResponse({"detail": "Organization not found"}, status=404)
    rows = list(
        Member.objects.filter(
            organization=organization,
            role_assignments__role__kind="OWNER",
        )
        .distinct()
        .order_by("created_at", "id")
    )
    roles = roles_for(rows)
    return JsonResponse({"total": len(rows), "items": [member_data(member, roles) for member in rows]})


@require_GET
def invitations(request, organization_id):
    """Safe invitation metadata only; hashes and opaque invitation tokens stay private."""
    denied = authorize(request)
    if denied is not None:
        return denied
    organization = Organization.objects.filter(id=organization_id).first()
    if organization is None:
        return JsonResponse({"detail": "Organization not found"}, status=404)
    values, error = pagination(request)
    if error:
        return error
    limit, offset = values
    query = Invitation.objects.filter(organization=organization).select_related("intended_role")
    total = query.count()
    items = [
        {
            "id": str(row.id),
            "recipient_name": row.recipient_name,
            "recipient_email": row.recipient_email or None,
            "role": row.intended_role.kind,
            "status": row.status,
            "created_at": row.created_at.isoformat(),
            "expires_at": row.expires_at.isoformat(),
        }
        for row in query.order_by("created_at", "id")[offset : offset + limit]
    ]
    return JsonResponse({"total": total, "items": items})


@require_GET
def security_summary(request, organization_id):
    """Factual tenant security metadata; deliberately no score or recommendations."""
    denied = authorize(request)
    if denied is not None:
        return denied
    organization = Organization.objects.filter(id=organization_id).first()
    if organization is None:
        return JsonResponse({"detail": "Organization not found"}, status=404)
    member_counts = {
        row["status"]: row["count"]
        for row in Member.objects.filter(organization=organization)
        .values("status")
        .annotate(count=Count("id"))
    }
    invitation_counts = {
        row["status"]: row["count"]
        for row in Invitation.objects.filter(organization=organization)
        .values("status")
        .annotate(count=Count("id"))
    }
    role_counts = {
        row["role__kind"]: row["count"]
        for row in RoleAssignment.objects.filter(
            organization=organization,
            member__status=Member.Status.ACTIVE,
        )
        .values("role__kind")
        .annotate(count=Count("member", distinct=True))
    }
    return JsonResponse(
        {
            "owners": role_counts.get("OWNER", 0),
            "administrators": role_counts.get("ADMIN", 0),
            "active_members": member_counts.get(Member.Status.ACTIVE, 0),
            "inactive_members": sum(
                count for status, count in member_counts.items() if status != Member.Status.ACTIVE
            ),
            "member_statuses": member_counts,
            "invitation_statuses": invitation_counts,
        }
    )
