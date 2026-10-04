"""Server-authoritative conversation authorization, including tenant and block checks."""

from uuid import UUID

import httpx

from app.auth import Principal
from app.core import ProtocolError, settings


class ConversationAuthorizer:
    async def authorize(self, principal: Principal, conversation_id: UUID) -> None:
        configured = settings()
        if not configured.conversation_service_url or not configured.internal_service_token:
            raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.")
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
                response = await client.post(
                    f"{configured.conversation_service_url.rstrip('/')}/internal/v1/conversations/{conversation_id}/authorize",
                    headers={"X-Internal-Service-Token": configured.internal_service_token},
                    json={
                        "organization_id": str(principal.organization_id),
                        "member_id": str(principal.member_id),
                    },
                )
            response.raise_for_status()
            data = response.json()
            if (
                data.get("allowed") is True
                and data.get("organization_id") == str(principal.organization_id)
                and data.get("member_id") == str(principal.member_id)
                and data.get("conversation_id") == str(conversation_id)
            ):
                return
        except (httpx.HTTPError, ValueError, TypeError):
            pass
        raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.")


class StaticAuthorizer(ConversationAuthorizer):
    def __init__(self, allowed=()):
        self.allowed = set(allowed)

    async def authorize(self, principal, conversation_id):
        if (principal.organization_id, principal.member_id, conversation_id) not in self.allowed:
            raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.")
