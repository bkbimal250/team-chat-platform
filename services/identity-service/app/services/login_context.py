"""Resolve tenant context for authentication without coupling personal login to membership."""

from uuid import UUID

from app.core.errors import DomainError
from app.integrations.organization_service import OrganizationServiceClient


async def resolve_workspace_session_context(
    identity_id: UUID,
    organization_id: UUID | None,
    correlation_id: str,
) -> tuple[UUID | None, UUID | None]:
    """Return a personal session when no organization is selected; otherwise require active membership."""
    if organization_id is None:
        return None, None
    memberships = await OrganizationServiceClient().memberships(identity_id, correlation_id)
    active = [
        item
        for item in memberships
        if item.status == "ACTIVE" and item.organization_id == organization_id
    ]
    if len(active) != 1:
        raise DomainError(
            "MEMBERSHIP_INACTIVE", "The requested organization context is unavailable.", 403
        )
    selected = active[0]
    return selected.organization_id, selected.member_id
