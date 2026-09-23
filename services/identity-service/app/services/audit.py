from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import OutboxEvent, SecurityAuditEvent


async def audit_and_event(
    session: AsyncSession,
    *,
    action: str,
    event_type: str,
    aggregate_type: str,
    aggregate_id: UUID,
    correlation_id: str,
    identity_id: UUID | None = None,
    organization_id: UUID | None = None,
    member_id: UUID | None = None,
    device_id: UUID | None = None,
    session_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str = "",
    changed_fields: list[str] | None = None,
) -> None:
    session.add(
        SecurityAuditEvent(
            identity_id=identity_id,
            organization_id=organization_id,
            member_id=member_id,
            device_id=device_id,
            session_id=session_id,
            action=action,
            metadata_={"changed_fields": changed_fields or []},
            ip_address=ip_address,
            user_agent=user_agent[:512],
            correlation_id=correlation_id,
        )
    )
    session.add(
        OutboxEvent(
            event_type=event_type,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            organization_id=organization_id,
            correlation_id=correlation_id,
            payload={
                "resource_id": str(aggregate_id),
                "changed_fields": changed_fields or [],
                "status": "ACTIVE",
            },
        )
    )
