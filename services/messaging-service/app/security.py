from dataclasses import dataclass
from uuid import UUID

import jwt
from fastapi import Header

from app.core import DomainError, settings


@dataclass(frozen=True)
class Principal:
    user_id: UUID
    member_id: UUID
    device_id: UUID
    organization_id: UUID


async def principal(authorization: str = Header(...)) -> Principal:
    try:
        token = authorization.removeprefix("Bearer ")
        s = settings()
        claims = jwt.decode(
            token,
            s.jwt_public_key,
            algorithms=[s.jwt_algorithm],
            issuer=s.jwt_issuer,
            audience=s.jwt_audience,
            options={"require": ["sub", "mid", "did", "org", "exp"]},
        )
        return Principal(
            UUID(claims["sub"]), UUID(claims["mid"]), UUID(claims["did"]), UUID(claims["org"])
        )
    except Exception as exc:
        raise DomainError("ACCESS_TOKEN_INVALID", "Authentication is required.", 401) from exc
