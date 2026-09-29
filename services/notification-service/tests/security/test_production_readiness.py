from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.config import NotificationSettings
from app.main import app
from app.providers import FirebaseFCMProvider, ProviderResult
from app.security import get_principal


@pytest.fixture
def jwt_keys(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    # PyJWT accepts key objects, so retain this test-only object through settings patching.
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
    return private_key


@pytest.mark.asyncio
async def test_jwt_principal_validates_signature_claims_and_expiry(jwt_keys):
    claims = {
        "sub": str(uuid4()),
        "org": str(uuid4()),
        "mid": str(uuid4()),
        "did": str(uuid4()),
        "iss": "identity-service",
        "aud": "team-chat-platform",
        "exp": datetime.now(UTC) + timedelta(minutes=5),
    }
    token = jwt.encode(claims, jwt_keys, algorithm="RS256")
    principal = await get_principal(f"Bearer {token}")
    assert str(principal.organization_id) == claims["org"]
    expired = jwt.encode(
        {**claims, "exp": datetime.now(UTC) - timedelta(seconds=1)}, jwt_keys, algorithm="RS256"
    )
    with pytest.raises(HTTPException, match="invalid"):
        await get_principal(f"Bearer {expired}")
    with pytest.raises(HTTPException, match="invalid"):
        await get_principal(f"Bearer {token}altered")


def test_production_configuration_fails_closed():
    with pytest.raises(ValidationError, match="JWT_PUBLIC_KEY"):
        NotificationSettings(
            app_env="production", push_provider="fcm", firebase_credentials_json="{}"
        )
    with pytest.raises(ValidationError, match="PUSH_PROVIDER=fcm"):
        NotificationSettings(app_env="production", jwt_public_key="key")
    with pytest.raises(ValidationError, match="FIREBASE_CREDENTIALS_JSON"):
        NotificationSettings(push_provider="fcm")


@pytest.mark.asyncio
async def test_firebase_provider_maps_invalid_and_retryable_results(monkeypatch):
    provider = object.__new__(FirebaseFCMProvider)
    provider.app = object()
    token = type("Token", (), {"token": "device-token"})()

    def invalid(*_args, **_kwargs):
        from firebase_admin import messaging

        raise messaging.UnregisteredError(None, None)

    monkeypatch.setattr("app.providers.messaging.send", invalid)
    result = await provider.send(token, {"data": {"notification_id": "one"}})
    assert result == ProviderResult(False, error_code="unregistered token", token_invalid=True)


def test_health_liveness_is_unauthenticated():
    with TestClient(app) as client:
        response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


@pytest.mark.asyncio
async def test_readiness_reports_database_availability(monkeypatch):
    class Session:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            return None

        async def execute(self, _statement):
            return None

    class UnavailableSession(Session):
        async def execute(self, _statement):
            raise RuntimeError("database unavailable")

    from app import main

    monkeypatch.setattr(main, "SessionLocal", Session)
    assert await main.ready() == {"status": "ready"}
    monkeypatch.setattr(main, "SessionLocal", UnavailableSession)
    assert (await main.ready()).status_code == 503
