import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt

from app.core.config import settings

# Load RSA keys directly from environment variables (PEM strings)
_PRIVATE_KEY = settings.ACCESS_TOKEN_PRIVATE_KEY
_PUBLIC_KEY = settings.ACCESS_TOKEN_PUBLIC_KEY
_ALGORITHM = settings.ACCESS_TOKEN_ALG


def _now() -> datetime:
    return datetime.now(timezone.utc)


def create_access_token(
    *,
    identity_id: uuid.UUID,
    session_id: uuid.UUID,
    device_id: uuid.UUID,
    organization_id: uuid.UUID | None = None,
    member_id: uuid.UUID | None = None,
    expires_delta: timedelta | None = None,
) -> str:
    now = _now()
    exp = now + (expires_delta or timedelta(seconds=settings.ACCESS_TOKEN_TTL))
    payload: Dict[str, Any] = {
        "sub": str(identity_id),
        "sid": str(session_id),
        "did": str(device_id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": settings.SERVICE_NAME,
        "aud": "team-chat-platform",
    }
    if organization_id:
        payload["org"] = str(organization_id)
    if member_id:
        payload["mid"] = str(member_id)
    token = jwt.encode(payload, _PRIVATE_KEY, algorithm=_ALGORITHM)
    return token


# Name retained for the session service's public token-issuance boundary.
issue_access_token = create_access_token


def decode_access_token(token: str) -> Dict[str, Any]:
    try:
        claims = jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=[_ALGORITHM],
            audience="team-chat-platform",
            issuer=settings.SERVICE_NAME,
            options={"require": ["sub", "sid", "did", "exp", "iat"]},
        )
        return claims
    except Exception as exc:
        from app.core.errors import DomainError

        raise DomainError("ACCESS_TOKEN_INVALID", "Invalid access token.", 401) from exc


def create_refresh_token(
    *, token_id: uuid.UUID, family_id: uuid.UUID, expires_delta: timedelta | None = None
) -> str:
    now = _now()
    exp = now + (expires_delta or timedelta(seconds=settings.REFRESH_TOKEN_TTL))
    payload = {
        "jti": str(token_id),
        "fid": str(family_id),
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
        "iss": settings.SERVICE_NAME,
        "aud": "team-chat-platform",
    }
    return jwt.encode(payload, _PRIVATE_KEY, algorithm=_ALGORITHM)


def decode_refresh_token(token: str) -> Dict[str, Any]:
    try:
        return jwt.decode(
            token,
            _PUBLIC_KEY,
            algorithms=[_ALGORITHM],
            audience="team-chat-platform",
            issuer=settings.SERVICE_NAME,
            options={"require": ["jti", "fid", "exp", "iat"]},
        )
    except Exception as exc:
        from app.core.errors import DomainError

        raise DomainError("REFRESH_TOKEN_INVALID", "Invalid refresh token.", 401) from exc
