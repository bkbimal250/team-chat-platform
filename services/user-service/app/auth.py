"""Shared downstream verification contract for Identity-issued access tokens."""

import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import get_settings

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    identity_id: uuid.UUID
    session_id: uuid.UUID
    device_id: uuid.UUID
    organization_id: uuid.UUID | None
    member_id: uuid.UUID | None


def require_authenticated_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "authentication required")
    try:
        settings = get_settings()
        claims = jwt.decode(
            credentials.credentials,
            settings.IDENTITY_JWT_PUBLIC_KEY,
            algorithms=[settings.IDENTITY_JWT_ALGORITHM],
            issuer=settings.IDENTITY_JWT_ISSUER,
            audience="team-chat-platform",
            options={"require": ["sub", "sid", "did", "exp", "iat"]},
        )
        if ("org" in claims) != ("mid" in claims):
            raise ValueError("Incomplete tenant context")
        return AuthContext(
            *(uuid.UUID(claims[key]) for key in ("sub", "sid", "did")),
            uuid.UUID(claims["org"]) if "org" in claims else None,
            uuid.UUID(claims["mid"]) if "mid" in claims else None,
        )
    except (KeyError, TypeError, ValueError, jwt.PyJWTError) as exc:
        raise HTTPException(401, "invalid access token") from exc
