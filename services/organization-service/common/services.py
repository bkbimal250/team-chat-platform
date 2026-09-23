from functools import wraps
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.audit.models import AuditLog
from apps.organizations.models import Organization
from common.authorization import require
from common.exceptions import DomainError
from common.selectors import tenant_get
from events.outbox.models import OutboxEvent
from events.schemas import EVENT_TYPES, ChangePayload


def command(function):
    """A command's domain changes, audit entries and events commit or roll back together."""

    @wraps(function)
    def wrapped(*args, **kwargs):
        try:
            with transaction.atomic():
                return function(*args, **kwargs)
        except IntegrityError as exc:
            constraint = getattr(getattr(exc.__cause__, "diag", None), "constraint_name", "")
            code = {
                "member_tenant_user": "MEMBER_ALREADY_EXISTS",
                "team_active_membership": "TEAM_MEMBERSHIP_EXISTS",
                "branch_active_membership": "BRANCH_MEMBERSHIP_EXISTS",
                "member_one_primary_branch": "PRIMARY_BRANCH_EXISTS",
                "branch_tenant_code": "BRANCH_CODE_EXISTS",
            }.get(constraint, "CONSTRAINT_CONFLICT")
            raise DomainError(
                code, "The operation conflicts with an existing resource or relationship."
            ) from None

    return wrapped


def lock_tenant(context, permission):
    require(context, permission)
    organization = Organization.objects.select_for_update().get(id=context.organization_id)
    if organization.status != Organization.Status.ACTIVE:
        raise DomainError("TENANT_INACTIVE", "Organization is not active.", 403)
    # Refresh permissions under the tenant lock, preventing stale authorization on writes.
    if context.member_id:
        from apps.members.models import Member
        from common.authorization import effective_permissions

        member = tenant_get(Member, context, context.member_id)
        if member.status != "ACTIVE" or permission not in effective_permissions(member):
            raise DomainError("PERMISSION_DENIED", "Permission denied.", 403)
    return organization


def validate_fields(instance):
    for name in ("timezone", "default_timezone"):
        value = getattr(instance, name, None)
        if value:
            try:
                ZoneInfo(value)
            except (ZoneInfoNotFoundError, ValueError):
                raise DomainError(
                    "INVALID_TIMEZONE", "Provide a valid IANA timezone.", 400
                ) from None
    for name in ("country", "country_code"):
        value = getattr(instance, name, None)
        if value is not None and (len(value) != 2 or not value.isalpha() or value != value.upper()):
            raise DomainError(
                "INVALID_COUNTRY_CODE", "Use a two-letter uppercase country code.", 400
            )
    instance.full_clean(validate_unique=False, validate_constraints=False)


def validate_relations(context, instance):
    """Validate all tenant-owned FK targets. Composite PostgreSQL FKs are the backstop."""
    for field in instance._meta.fields:
        if not field.is_relation or field.name == "organization":
            continue
        target = field.remote_field.model
        value = getattr(instance, field.attname)
        if value and hasattr(target, "organization_id"):
            tenant_get(target, context, value)


def record(context, instance, aggregate: str, action: str, fields=()):
    event_type = f"{aggregate}.{action}.v1"
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unregistered event: {event_type}")
    payload = ChangePayload(
        resource_id=instance.id,
        changed_fields=sorted(fields),
        status=getattr(instance, "status", None),
    )
    AuditLog.objects.create(
        organization_id=context.organization_id,
        actor_user_id=context.user_id,
        actor_member_id=context.member_id,
        action=f"{aggregate}_{action}".upper(),
        resource_type=aggregate,
        resource_id=instance.id,
        metadata={"changed_fields": sorted(fields)},
        correlation_id=context.correlation_id,
        ip_address=context.ip_address,
        user_agent=context.user_agent,
    )
    OutboxEvent.objects.create(
        event_type=event_type,
        aggregate_type=aggregate,
        aggregate_id=instance.id,
        organization_id=context.organization_id,
        correlation_id=context.correlation_id,
        payload=payload.model_dump(mode="json"),
    )


def enforce_capacity(organization, model):
    from apps.members.models import Member
    from apps.teams.models import Team

    field = {Member: "max_members", Team: "max_teams"}.get(model)
    if field:
        limit = getattr(organization.settings, field)
        excluded = ["REMOVED", "LEFT"] if model is Member else ["DELETED"]
        if (
            limit is not None
            and model.objects.filter(organization=organization).exclude(status__in=excluded).count()
            >= limit
        ):
            raise DomainError(
                "TENANT_LIMIT_REACHED", "The configured organization capacity has been reached."
            )


@command
def create_resource(context, model, data, aggregate):
    organization = lock_tenant(context, f"{aggregate}.create")
    enforce_capacity(organization, model)
    values = dict(data)
    values.pop("organization_id", None)
    if aggregate == "team":
        values["created_by_member_id"] = context.member_id
    if aggregate == "member":
        values["status"] = "INVITED"
    instance = model(organization=organization, **values)
    validate_relations(context, instance)
    validate_fields(instance)
    instance.save()
    record(context, instance, aggregate, "created", values)
    return instance


@command
def update_resource(context, model, pk, data, aggregate):
    lock_tenant(context, f"{aggregate}.update")
    instance = tenant_get(model, context, pk, lock=True)
    if getattr(instance, "status", None) in {"DELETED", "REMOVED", "LEFT"}:
        raise DomainError("RESOURCE_TERMINAL", "A terminal resource cannot be updated.")
    for field, value in data.items():
        setattr(instance, field, value)
    validate_relations(context, instance)
    validate_fields(instance)
    instance.save()
    record(context, instance, aggregate, "updated", data)
    return instance


@command
def transition(context, model, pk, status, aggregate):
    permission = (
        f"{aggregate}.remove"
        if aggregate == "member" and status in {"REMOVED", "LEFT"}
        else f"{aggregate}.delete"
        if status == "DELETED"
        else f"{aggregate}.update"
    )
    lock_tenant(context, permission)
    instance = tenant_get(model, context, pk, lock=True)
    allowed = (
        {
            "INVITED": {"ACTIVE", "REMOVED"},
            "ACTIVE": {"SUSPENDED", "LEFT", "REMOVED"},
            "SUSPENDED": {"ACTIVE", "REMOVED", "LEFT"},
        }
        if aggregate == "member"
        else {"ACTIVE": {"DISABLED", "DELETED"}, "DISABLED": {"ACTIVE", "DELETED"}}
    )
    if status not in allowed.get(instance.status, set()):
        raise DomainError("INVALID_TRANSITION", "This lifecycle transition is not allowed.")
    if aggregate == "member":
        from apps.members.services import protect_last_owner

        if status != "ACTIVE":
            protect_last_owner(instance)
        if status == "ACTIVE":
            if not instance.user_id:
                raise DomainError(
                    "IDENTITY_REQUIRED", "Activation requires a linked platform user."
                )
            instance.joined_at = instance.joined_at or timezone.now()
            instance.suspended_at = None
        elif status == "SUSPENDED":
            instance.suspended_at = timezone.now()
        else:
            instance.left_at = timezone.now()
            from apps.branches.models import BranchMembership
            from apps.teams.models import TeamMembership

            TeamMembership.objects.filter(member=instance, status="ACTIVE").update(
                status="LEFT", left_at=timezone.now()
            )
            BranchMembership.objects.filter(member=instance, left_at__isnull=True).update(
                left_at=timezone.now(), is_primary=False
            )
    instance.status = status
    instance.save()
    action = {
        "ACTIVE": "activated" if aggregate == "member" else "updated",
        "SUSPENDED": "suspended",
        "REMOVED": "removed",
        "LEFT": "left",
        "DISABLED": "disabled",
        "DELETED": "deleted",
    }[status]
    record(context, instance, aggregate, action, ["status"])
    return instance
