"""Workspace org-member projection for delivery and subscription gates."""

from uuid import UUID

INACTIVE = frozenset({"LEFT", "REMOVED", "SUSPENDED"})


class OrgMembershipStore:
    def __init__(self):
        self.status = {}

    def _key(self, organization_id: UUID, member_id: UUID) -> tuple[UUID, UUID]:
        return (organization_id, member_id)

    async def set_status(self, organization_id: UUID, member_id: UUID, status: str) -> None:
        self.status[self._key(organization_id, member_id)] = status.upper()

    async def get_status(self, organization_id: UUID, member_id: UUID) -> str | None:
        return self.status.get(self._key(organization_id, member_id))

    async def is_active(self, organization_id: UUID, member_id: UUID) -> bool:
        status = await self.get_status(organization_id, member_id)
        return status is None or status == "ACTIVE"

    def org_member_key(self, organization_id: UUID, member_id: UUID) -> str:
        return f"realtime:org-member:{organization_id}:{member_id}"


class RedisOrgMembershipStore(OrgMembershipStore):
    def __init__(self, redis):
        super().__init__()
        self.redis = redis

    async def set_status(self, organization_id: UUID, member_id: UUID, status: str) -> None:
        await super().set_status(organization_id, member_id, status)
        await self.redis.set(self.org_member_key(organization_id, member_id), status.upper())

    async def get_status(self, organization_id: UUID, member_id: UUID) -> str | None:
        cached = await self.redis.get(self.org_member_key(organization_id, member_id))
        if cached is None:
            return await super().get_status(organization_id, member_id)
        return cached.decode() if isinstance(cached, bytes) else str(cached)
