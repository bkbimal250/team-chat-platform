from uuid import UUID

from app.auth import Principal
from app.core import ProtocolError


class ConversationAuthorizer:
    """Fail-closed boundary for a local projection or Phase 4 internal client."""

    async def authorize(self, principal: Principal, conversation_id: UUID) -> None:
        raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.")


class StaticAuthorizer(ConversationAuthorizer):
    def __init__(self, allowed=()):
        self.allowed = set(allowed)

    async def authorize(self, principal, conversation_id):
        if (principal.organization_id, principal.member_id, conversation_id) not in self.allowed:
            await super().authorize(principal, conversation_id)
