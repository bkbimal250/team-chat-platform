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


async def get_principal(authorization: str | None = Header(default=None)) -> Principal:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(401, "authentication is required")
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
            options={"require": ["sub", "did", "exp"]},
        )
        if ("org" in claims) != ("mid" in claims):
            raise ValueError("Incomplete tenant context")
        organization_id = UUID(claims["org"]) if "org" in claims else None
        member_id = UUID(claims["mid"]) if "mid" in claims else UUID(claims["sub"])
        return Principal(
            organization_id=organization_id,
            user_id=UUID(claims["sub"]),
            member_id=member_id,
            device_id=UUID(claims["did"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, "invalid authentication") from exc
