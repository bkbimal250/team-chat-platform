"""Identity-only invitation validation and atomic phone-bound membership acceptance."""

import hashlib
import hmac
import json
from uuid import UUID

from django.conf import settings
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from apps.branches.models import Branch
from apps.invitations.membership import (
    DEPARTED_MEMBER_STATUSES,
    create_member_from_invitation,
    rejoin_member_from_invitation,
)
from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.organizations.models import Organization
from apps.roles.services import check_delegation
from apps.teams.models import Team
from common.authorization import effective_permissions
from common.context import TenantContext
from common.exceptions import DomainError
from common.services import lock_tenant, record, validate_relations


def digest(token):
    return hashlib.sha256(token.encode()).hexdigest()


def available(invitation, *, completed=False):
    if invitation.status == "ACCEPTED" and completed:
        return
    if invitation.status != "PENDING":
        raise DomainError(
            "INVITATION_" + invitation.status, "This invitation is no longer available.", 410
        )
    if invitation.expires_at <= timezone.now():
        raise DomainError("INVITATION_EXPIRED", "This invitation has expired.", 410)
    if invitation.organization.status != "ACTIVE":
        raise DomainError("INVITATION_UNAVAILABLE", "This workspace is unavailable.", 403)


def snapshot(invitation):
    return {
        "invitation_id": str(invitation.id),
        "organization_id": str(invitation.organization_id),
        "company_name": invitation.organization.name,
        "recipient_name": invitation.recipient_name,
        "phone": invitation.recipient_phone,
        "email": invitation.recipient_email,
        "expires_at": invitation.expires_at.isoformat(),
    }


@transaction.atomic
def accept_bound(invitation_id, token_hash, phone, identity_id, correlation_id, *, email=None):
    # All invitation/role/membership changes serialize on the tenant before the invitation.
    reference = Invitation.objects.filter(id=invitation_id, token_hash=token_hash).first()
    if reference is None:
        raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
    Organization.objects.select_for_update().get(id=reference.organization_id)
    invitation = (
        Invitation.objects.select_for_update(of=("self",))
        .select_related("organization", "invited_by_member", "intended_role")
        .get(id=reference.id)
    )
    if (
        not hmac.compare_digest(invitation.token_hash or "", token_hash)
        or (email is None and invitation.recipient_phone != phone)
        or (
            email is not None
            and (
                not invitation.recipient_email
                or invitation.recipient_email.strip().lower() != email
            )
        )
    ):
        raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
    if invitation.status == "ACCEPTED":
        member = invitation.accepted_member
        if (
            member
            and member.user_id == identity_id
            and member.status == "ACTIVE"
            and invitation.organization.status == "ACTIVE"
        ):
            return {"organization_id": str(invitation.organization_id), "member_id": str(member.id)}
        raise DomainError("INVITATION_ACCEPTED", "This invitation has already been accepted.", 409)
    available(invitation)
    inviter = invitation.invited_by_member
    context = TenantContext(
        invitation.organization_id,
        inviter.id,
        inviter.user_id,
        effective_permissions(inviter),
        correlation_id,
    )
    organization = lock_tenant(context, "invitation.create")
    if not organization.settings.allow_member_invites:
        raise DomainError("INVITES_DISABLED", "Member invitations are disabled.", 403)
    check_delegation(context, invitation.intended_role)
    validate_relations(context, invitation)
    for model, pk in [(Branch, invitation.branch_id), (Team, invitation.team_id)]:
        if (
            pk
            and not model.objects.filter(id=pk, organization=organization, status="ACTIVE").exists()
        ):
            raise DomainError(
                "INACTIVE_MEMBERSHIP_TARGET", "The invitation assignment is unavailable.", 409
            )
    member = (
        Member.objects.select_for_update()
        .filter(organization=organization, user_id=identity_id)
        .first()
    )
    if member is None:
        member = create_member_from_invitation(context, invitation, identity_id)
    elif member.status in DEPARTED_MEMBER_STATUSES:
        member = rejoin_member_from_invitation(context, invitation, member)
    elif member.status != Member.Status.ACTIVE:
        raise DomainError(
            "MEMBER_INACTIVE", "Contact your administrator about this membership.", 403
        )
    invitation.status, invitation.accepted_at, invitation.accepted_member = (
        "ACCEPTED",
        timezone.now(),
        member,
    )
    invitation.save()
    record(context, invitation, "invitation", "accepted", ["status", "accepted_member_id"])
    return {"organization_id": str(organization.id), "member_id": str(member.id)}


@require_POST
@csrf_exempt
def invitation_onboarding(request, action):
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        body = json.loads(request.body)
        if action == "validate" and set(body) == {"token"}:
            token = body["token"]
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            invitation = (
                Invitation.objects.select_related("organization")
                .filter(token_hash=digest(token))
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            available(invitation)
            return JsonResponse(snapshot(invitation))
        if action == "resume" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            invitation = (
                Invitation.objects.select_related("organization", "accepted_member")
                .filter(
                    id=UUID(body["invitation_id"]),
                    token_hash=body["token_hash"],
                    recipient_phone=body["phone"],
                    status="ACCEPTED",
                    accepted_member__user_id=UUID(body["identity_id"]),
                    accepted_member__status="ACTIVE",
                    organization__status="ACTIVE",
                )
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            return JsonResponse(snapshot(invitation))
        if action == "accept-email" and set(body) == {
            "invitation_id",
            "token_hash",
            "email",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    None,
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                    email=body["email"],
                )
            )
        if action == "accept" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    body["phone"],
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                )
            )
        raise ValueError()
    except DomainError as exc:
        return JsonResponse(
            {"error": {"code": exc.machine_code, "message": str(exc.detail)}},
            status=exc.status_code,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": {"code": "INVITATION_INVALID", "message": "This invitation is invalid."}},
            status=400,
        )
