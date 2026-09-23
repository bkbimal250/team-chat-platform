import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.auth import require_authenticated_context


@pytest.fixture
def token_factory(monkeypatch):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private = key.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
    public = key.public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo).decode()
    monkeypatch.setenv("IDENTITY_JWT_PUBLIC_KEY", public)
    monkeypatch.setenv("IDENTITY_JWT_ISSUER", "identity-service")

    def make(**changes):
        now = datetime.now(UTC)
        data = {
            "sub": str(uuid.uuid4()),
            "sid": str(uuid.uuid4()),
            "did": str(uuid.uuid4()),
            "org": str(uuid.uuid4()),
            "mid": str(uuid.uuid4()),
            "iss": "identity-service",
            "aud": "team-chat-platform",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        data.update(changes)
        return jwt.encode(data, private, algorithm="RS256")

    return make


def test_valid_jwt_creates_trusted_context(token_factory):
    context = require_authenticated_context(
        HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_factory())
    )
    assert context.organization_id and context.member_id


@pytest.mark.parametrize(
    "changes",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
        {"iss": "wrong"},
        {"aud": "wrong"},
        {"org": None},
        {"mid": None},
    ],
)
def test_invalid_jwt_claims_are_rejected(token_factory, changes):
    with pytest.raises(HTTPException) as error:
        require_authenticated_context(
            HTTPAuthorizationCredentials(scheme="Bearer", credentials=token_factory(**changes))
        )
    assert error.value.status_code == 401
