import hashlib
import secrets
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from apps.invitations.delivery import delivery_provider
from apps.invitations.models import Invitation
from apps.members.models import Member
from apps.roles.models import Role, RoleAssignment
from apps.roles.services import check_delegation
from apps.teams.services import add_membership
from common.exceptions import DomainError
from common.selectors import tenant_get
from common.services import command, lock_tenant, record, validate_fields, validate_relations


@command
def create_invitation(context, data):
    organization = lock_tenant(context, "invitation.create")
    if not organization.settings.allow_member_invites:
        raise DomainError("INVITES_DISABLED", "Member invitations are disabled.", 403)
    role = tenant_get(Role, context, data["intended_role_id"])
    check_delegation(context, role)
    data = dict(data)
    token = None
    if data.get("recipient_email"):
        from django.core.exceptions import ValidationError
        from django.core.validators import validate_email

        data["recipient_email"] = data["recipient_email"].strip().lower()
        try:
            validate_email(data["recipient_email"])
        except ValidationError:
            raise DomainError("EMAIL_INVALID", "Provide a valid email address.", 400) from None
        if len(data.get("recipient_name", "").strip()) < 2:
            raise DomainError("NAME_INVALID", "Provide an employee name.", 400)
        if Invitation.objects.filter(
            organization=organization,
            recipient_email=data["recipient_email"],
            status="PENDING",
            expires_at__gt=timezone.now(),
        ).exists():
            raise DomainError(
                "INVITATION_PENDING", "An invitation is already pending for this recipient.", 409
            )
        token = secrets.token_urlsafe(32)
        development_url = delivery_provider().deliver(token)
        data["token_hash"] = hashlib.sha256(token.encode()).hexdigest()
    if data.get("recipient_phone"):
        import phonenumbers

        try:
            parsed = phonenumbers.parse(data["recipient_phone"], None)
        except phonenumbers.NumberParseException:
            raise DomainError(
                "PHONE_INVALID", "Provide a valid international phone number.", 400
            ) from None
        if not phonenumbers.is_valid_number(parsed):
            raise DomainError("PHONE_INVALID", "Provide a valid international phone number.", 400)
        data["recipient_phone"] = phonenumbers.format_number(
            parsed, phonenumbers.PhoneNumberFormat.E164
        )
        if len(data.get("recipient_name", "").strip()) < 2:
            raise DomainError("NAME_INVALID", "Provide an employee name.", 400)
        data["recipient_name"] = data["recipient_name"].strip()
        data["recipient_email"] = data.get("recipient_email", "").strip().lower()
        Invitation.objects.filter(
            organization=organization,
            status="PENDING",
            recipient_phone=data["recipient_phone"],
            expires_at__lte=timezone.now(),
        ).update(status="EXPIRED")
        if Invitation.objects.filter(
            organization=organization, status="PENDING", recipient_phone=data["recipient_phone"]
        ).exists():
            raise DomainError(
                "INVITATION_PENDING", "An invitation is already pending for this recipient."
            )
        if Invitation.objects.filter(
            organization=organization,
            status="ACCEPTED",
            recipient_phone=data["recipient_phone"],
            accepted_member__status="ACTIVE",
        ).exists():
            raise DomainError(
                "MEMBER_ALREADY_EXISTS", "This recipient is already an active member."
            )
        token = secrets.token_urlsafe(32)
        # Fail before creating a row if production delivery is unconfigured.
        development_url = delivery_provider().deliver(token)
        data["token_hash"] = hashlib.sha256(token.encode()).hexdigest()
    elif not data.get("recipient_email") and data.get("recipient_name"):
        raise DomainError("PHONE_REQUIRED", "Phone is required for employee invitations.", 400)
    data.setdefault("expires_at", timezone.now() + timedelta(hours=settings.INVITATION_TTL_HOURS))
    if data["expires_at"] <= timezone.now():
        raise DomainError("INVALID_EXPIRY", "Invitation expiry must be in the future.", 400)
    invitation = Invitation(
        organization=organization, invited_by_member_id=context.member_id, **data
    )
    validate_relations(context, invitation)
    if invitation.recipient_phone or invitation.recipient_email:
        if invitation.expires_at > timezone.now() + timedelta(hours=settings.INVITATION_TTL_HOURS):
            raise DomainError(
                "INVALID_EXPIRY", "Invitation expiry exceeds the configured lifetime.", 400
            )
        for target in [invitation.branch, invitation.team]:
            if target and target.status != "ACTIVE":
                raise DomainError(
                    "INACTIVE_MEMBERSHIP_TARGET", "Choose an active branch/team.", 400
                )
        if (
            invitation.branch_id
            and invitation.team_id
            and invitation.team.branch_id not in {None, invitation.branch_id}
        ):
            raise DomainError(
                "INVALID_MEMBERSHIP_TARGET", "The team belongs to a different branch.", 400
            )
    validate_fields(invitation)
    invitation.save()
    record(context, invitation, "invitation", "created")
    if token:
        invitation.development_url = development_url
    return invitation


@command
def revoke_invitation(context, pk):
    lock_tenant(context, "invitation.revoke")
    invitation = tenant_get(Invitation, context, pk, lock=True)
    if invitation.status == "REVOKED":
        return invitation
    if invitation.status != "PENDING":
        raise DomainError("INVITATION_NOT_PENDING", "Only pending invitations can be revoked.")
    invitation.status = "REVOKED"
    invitation.revoked_at = timezone.now()
    invitation.save()
    record(context, invitation, "invitation", "revoked")
    return invitation


@command
def accept_invitation(context, pk, member_id):
    """Trusted business command; no QR, token or credential handling."""
    lock_tenant(context, "invitation.accept")
    invitation = tenant_get(Invitation, context, pk, lock=True)
    if invitation.status == "ACCEPTED" and invitation.accepted_member_id == member_id:
        return invitation
    if invitation.status != "PENDING" or invitation.expires_at <= timezone.now():
        raise DomainError("INVITATION_UNAVAILABLE", "Invitation is no longer available.")
    if invitation.recipient_phone or invitation.recipient_email:
        raise DomainError(
            "PHONE_VERIFICATION_REQUIRED",
            "Employee invitations require recipient OTP verification.",
            403,
        )
    member = tenant_get(Member, context, member_id, lock=True)
    if member.status != "ACTIVE":
        raise DomainError(
            "MEMBER_INACTIVE", "Invitation acceptance requires an active linked member."
        )
    check_delegation(context, invitation.intended_role)
    _, assigned = RoleAssignment.objects.get_or_create(
        organization_id=context.organization_id, member=member, role=invitation.intended_role
    )
    if assigned:
        record(context, member, "member", "role_changed", ["roles"])
    if invitation.team_id:
        add_membership(context, invitation.team_id, member.id)
    if invitation.branch_id:
        add_membership(context, invitation.branch_id, member.id, branch=True)
    invitation.status = "ACCEPTED"
    invitation.accepted_at = timezone.now()
    invitation.accepted_member = member
    invitation.save()
    record(context, invitation, "invitation", "accepted", ["status", "accepted_member_id"])
    return invitation


@command
def resend_invitation(context, pk):
    organization = lock_tenant(context, "invitation.create")
    if not organization.settings.allow_member_invites:
        raise DomainError("INVITES_DISABLED", "Member invitations are disabled.", 403)
    invitation = tenant_get(Invitation, context, pk, lock=True)
    if (
        invitation.status != "PENDING"
        or invitation.expires_at <= timezone.now()
        or not invitation.recipient_phone
    ):
        raise DomainError(
            "INVITATION_UNAVAILABLE", "Only valid pending employee invitations can be resent."
        )
    check_delegation(context, invitation.intended_role)
    token = secrets.token_urlsafe(32)
    url = delivery_provider().deliver(token)
    invitation.token_hash = hashlib.sha256(token.encode()).hexdigest()
    invitation.expires_at = timezone.now() + timedelta(hours=settings.INVITATION_TTL_HOURS)
    invitation.save()
    record(context, invitation, "invitation", "created", ["delivery_rotated"])
    invitation.development_url = url
    return invitation
