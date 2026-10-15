from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException

from app.security import get_principal


@pytest.mark.asyncio
async def test_personal_jwt_without_org(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        "app.security.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "jwt_public_key": private_key.public_key(),
                "jwt_algorithm": "RS256",
                "jwt_issuer": "identity-service",
                "jwt_audience": "team-chat-platform",
            },
        )(),
    )
    claims = {
        "sub": str(uuid4()),
        "sid": str(uuid4()),
        "did": str(uuid4()),
        "iss": "identity-service",
        "aud": "team-chat-platform",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    principal = await get_principal(f"Bearer {token}")
    assert principal.organization_id is None
    assert principal.member_id == principal.user_id


@pytest.mark.asyncio
async def test_incomplete_tenant_claims_rejected(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(
        "app.security.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "jwt_public_key": private_key.public_key(),
                "jwt_algorithm": "RS256",
                "jwt_issuer": "identity-service",
                "jwt_audience": "team-chat-platform",
            },
        )(),
    )
    claims = {
        "sub": str(uuid4()),
        "org": str(uuid4()),
        "did": str(uuid4()),
        "iss": "identity-service",
        "aud": "team-chat-platform",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, private_key, algorithm="RS256")
    with pytest.raises(HTTPException):
        await get_principal(f"Bearer {token}")
