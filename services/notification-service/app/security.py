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
            options={"require": ["sub", "mid", "did", "org", "exp"]},
        )
        return Principal(
            organization_id=UUID(claims["org"]),
            user_id=UUID(claims["sub"]),
            member_id=UUID(claims["mid"]),
            device_id=UUID(claims["did"]),
        )
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        raise HTTPException(401, "invalid authentication") from exc
