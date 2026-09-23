"""Shared downstream verification contract for Identity-issued access tokens."""

import os
import uuid
from dataclasses import dataclass

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthContext:
    identity_id: uuid.UUID
    session_id: uuid.UUID
    device_id: uuid.UUID
    organization_id: uuid.UUID
    member_id: uuid.UUID


def require_authenticated_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> AuthContext:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(401, "authentication required")
    try:
        claims = jwt.decode(
            credentials.credentials,
            os.environ["IDENTITY_JWT_PUBLIC_KEY"],
            algorithms=[os.getenv("IDENTITY_JWT_ALGORITHM", "RS256")],
            issuer=os.getenv("IDENTITY_JWT_ISSUER", "identity-service"),
            audience="team-chat-platform",
            options={"require": ["sub", "sid", "did", "org", "mid", "exp", "iat"]},
        )
        return AuthContext(*(uuid.UUID(claims[key]) for key in ("sub", "sid", "did", "org", "mid")))
    except (KeyError, ValueError, jwt.PyJWTError) as exc:
        raise HTTPException(401, "invalid access token") from exc
