"""Workspace membership revocation mirrored from Organization events."""

from uuid import UUID


class OrgMembershipGate:
    def __init__(self):
        self.revoked: set[tuple[UUID, UUID]] = set()

    def revoke(self, organization_id: UUID, member_id: UUID) -> None:
        self.revoked.add((organization_id, member_id))

    def reactivate(self, organization_id: UUID, member_id: UUID) -> None:
        self.revoked.discard((organization_id, member_id))

    def is_active(self, organization_id: UUID | None, member_id: UUID) -> bool:
        if organization_id is None:
            return True
        return (organization_id, member_id) not in self.revoked
