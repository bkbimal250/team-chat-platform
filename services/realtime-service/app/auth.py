from dataclasses import dataclass
from uuid import UUID

import jwt

from app.core import ProtocolError, settings


@dataclass(frozen=True)
class Principal:
    identity_id: UUID
    session_id: UUID
    device_id: UUID
    organization_id: UUID | None
    member_id: UUID


def authenticate(token: str) -> Principal:
    try:
        s = settings()
        claims = jwt.decode(
            token,
            s.jwt_public_key,
            algorithms=[s.jwt_algorithm],
            issuer=s.jwt_issuer,
            audience=s.jwt_audience,
            options={"require": ["sub", "sid", "did", "exp"]},
        )
        if ("org" in claims) != ("mid" in claims):
            raise ValueError("Incomplete tenant context")
        return Principal(
            UUID(claims["sub"]),
            UUID(claims["sid"]),
            UUID(claims["did"]),
            UUID(claims["org"]) if "org" in claims else None,
            UUID(claims["mid"]) if "mid" in claims else UUID(claims["sub"]),
        )
    except Exception as exc:
        raise ProtocolError("AUTH_INVALID", "Authentication failed.") from exc
