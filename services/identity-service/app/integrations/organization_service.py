from dataclasses import dataclass
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.errors import DomainError


@dataclass(frozen=True)
class MembershipContext:
    organization_id: UUID
    member_id: UUID
    status: str


class OrganizationServiceClient:
    """Only organization-service HTTP contract. Never imports its models or database."""

    def __init__(self):
        settings = get_settings()
        self.base_url = str(settings.organization_service_url).rstrip("/")
        self.token = settings.internal_service_token

    async def memberships(self, identity_id: UUID, correlation_id: str) -> list[MembershipContext]:
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(5.0, connect=2.0)) as client:
                response = await client.get(
                    f"{self.base_url}/api/internal/v1/identity-memberships/{identity_id}/",
                    headers={
                        "X-Internal-Service-Token": self.token,
                        "X-Correlation-ID": correlation_id,
                    },
                )
        except httpx.RequestError as exc:
            raise DomainError(
                "ORGANIZATION_SERVICE_UNAVAILABLE",
                "Membership verification is temporarily unavailable.",
                503,
            ) from exc
        if response.status_code == 401:
            raise RuntimeError("Organization service authentication rejected")
        if response.status_code >= 500:
            raise DomainError(
                "ORGANIZATION_SERVICE_UNAVAILABLE",
                "Membership verification is temporarily unavailable.",
                503,
            )
        if response.status_code != 200:
            raise DomainError(
                "MEMBERSHIP_UNAVAILABLE", "No active organization membership is available.", 403
            )
        return [
            MembershipContext(UUID(row["organization_id"]), UUID(row["member_id"]), row["status"])
            for row in response.json()["memberships"]
        ]

    async def validate_context(
        self, identity_id: UUID, organization_id: UUID, member_id: UUID, correlation_id: str
    ) -> MembershipContext:
        memberships = await self.memberships(identity_id, correlation_id)
        for item in memberships:
            if (
                item.organization_id == organization_id
                and item.member_id == member_id
                and item.status == "ACTIVE"
            ):
                return item
        raise DomainError("MEMBERSHIP_INACTIVE", "The organization membership is unavailable.", 403)
