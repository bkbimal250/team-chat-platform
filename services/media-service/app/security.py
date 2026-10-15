from dataclasses import dataclass, field
from uuid import UUID

import jwt
from fastapi import Header, HTTPException

from app.config import get_settings


@dataclass(frozen=True)
class Principal:
    organization_id: UUID | None
    user_id: UUID
    member_id: UUID
    device_id: UUID
    conversations: frozenset[UUID] = field(default_factory=frozenset)
    authorization: str | None = field(default=None, repr=False, compare=False)


async def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    """Derive trusted identity fields from an Identity-issued access token only."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "authentication required")
    settings = get_settings()
    if not settings.jwt_public_key:
        raise HTTPException(503, "JWT verification is not configured")
    try:
        claims = jwt.decode(
            authorization.removeprefix("Bearer "),
            settings.jwt_public_key,
            algorithms=[settings.jwt_algorithm],
            issuer=settings.jwt_issuer,
            audience=settings.jwt_audience,
            options={"require": ["sub", "sid", "did", "exp", "iat"]},
        )
        if ("org" in claims) != ("mid" in claims) or (
            "org" in claims and (not claims["org"] or not claims["mid"])
        ):
            raise ValueError("Incomplete tenant context")
        return Principal(
            UUID(claims["org"]) if "org" in claims else None,
            UUID(claims["sub"]),
            UUID(claims["mid"]) if "mid" in claims else UUID(claims["sub"]),
            UUID(claims["did"]),
            authorization=authorization,
        )
    except (jwt.PyJWTError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(401, "invalid trusted service context") from exc


def can_access(principal: Principal, conversation_id: UUID) -> bool:
    return conversation_id in principal.conversations


async def try_authorize_conversation(principal: Principal, conversation_id: UUID) -> bool:
    try:
        await authorize_conversation(principal, conversation_id)
    except HTTPException:
        return False
    return True


async def authorize_conversation(principal: Principal, conversation_id: UUID):
    if not principal.authorization:
        if not can_access(principal, conversation_id):
            raise HTTPException(403, "conversation access denied")
        return
    import asyncio
    import json
    from urllib.error import HTTPError, URLError
    from urllib.request import HTTPRedirectHandler, Request, build_opener

    configured = get_settings()
    if not configured.internal_service_token:
        raise HTTPException(503, "conversation authorization is not configured")

    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def check():
        request = Request(
            f"{configured.conversation_api_url.rstrip('/')}/internal/v1/conversations/{conversation_id}/authorize",
            data=json.dumps(
                {
                    "organization_id": str(principal.organization_id)
                    if principal.organization_id
                    else None,
                    "member_id": str(principal.member_id),
                    "identity_id": str(principal.user_id),
                }
            ).encode(),
            headers={
                "X-Internal-Service-Token": configured.internal_service_token,
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with build_opener(NoRedirect()).open(request, timeout=5) as response:
                data = json.loads(response.read(65536))
                if not isinstance(data, dict):
                    raise HTTPException(503, "conversation authorization response is invalid")
                if (
                    data.get("allowed") is not True
                    or data.get("conversation_id") != str(conversation_id)
                    or data.get("member_id") != str(principal.member_id)
                    or data.get("organization_id")
                    != (str(principal.organization_id) if principal.organization_id else None)
                    or data.get("user_id") != str(principal.user_id)
                ):
                    raise HTTPException(403, "conversation access denied")
        except HTTPError as exc:
            raise HTTPException(
                403 if exc.code in {401, 403, 404} else 503,
                "conversation access unavailable",
            ) from None
        except (URLError, TimeoutError, ValueError):
            raise HTTPException(503, "conversation authorization unavailable") from None

    await asyncio.to_thread(check)
