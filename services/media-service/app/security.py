from dataclasses import dataclass, field
from uuid import UUID

import jwt
from fastapi import Header, HTTPException

from app.config import get_settings


@dataclass(frozen=True)
class Principal:
    organization_id: UUID
    user_id: UUID
    member_id: UUID
    device_id: UUID
    conversations: frozenset[UUID] = field(default_factory=frozenset)


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
            options={"require": ["sub", "sid", "did", "org", "mid", "exp", "iat"]},
        )
        return Principal(
            UUID(claims["org"]),
            UUID(claims["sub"]),
            UUID(claims["mid"]),
            UUID(claims["did"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, "invalid trusted service context") from exc


def can_access(principal: Principal, conversation_id: UUID) -> bool:
    return conversation_id in principal.conversations
