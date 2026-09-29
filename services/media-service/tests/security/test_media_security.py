from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.main import app
from app.schemas import UploadRequest
from app.security import Principal, get_principal
from app.service import MediaService
from app.storage import FakePrivateStorage, ObjectInfo


def principal(org, conversation):
    return Principal(org, uuid4(), uuid4(), uuid4(), frozenset({conversation}))


@pytest.fixture
def identity_token_factory(monkeypatch):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = (
        private_key.public_key()
        .public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)
        .decode()
    )
    monkeypatch.setenv("JWT_PUBLIC_KEY", public_key)
    monkeypatch.setenv("JWT_ALGORITHM", "RS256")
    monkeypatch.setenv("JWT_ISSUER", "identity-service")
    monkeypatch.setenv("JWT_AUDIENCE", "team-chat-platform")

    def issue(**overrides):
        now = datetime.now(UTC)
        claims = {
            "sub": str(uuid4()),
            "sid": str(uuid4()),
            "did": str(uuid4()),
            "org": str(uuid4()),
            "mid": str(uuid4()),
            "iat": now,
            "exp": now + timedelta(minutes=5),
            "iss": "identity-service",
            "aud": "team-chat-platform",
        }
        claims.update(overrides)
        return jwt.encode(claims, private_key, algorithm="RS256"), claims

    return issue


@pytest.mark.asyncio
async def test_cross_tenant_lookup_download_and_delete_are_hidden():
    org, conversation = uuid4(), uuid4()
    owner = principal(org, conversation)
    service = MediaService(FakePrivateStorage())
    result = await service.initiate(
        owner,
        UploadRequest(
            conversation_id=conversation,
            filename="x.jpg",
            mime_type="image/jpeg",
            size_bytes=1,
            media_type="image",
        ),
    )
    media = service.media[result["media_id"]]
    service.storage.objects[(media.bucket, media.object_key)] = ObjectInfo(1, "image/jpeg")
    await service.complete(owner, media.id)
    intruder = principal(uuid4(), conversation)
    for action in (service.download, service.delete):
        with pytest.raises(HTTPException) as error:
            await action(intruder, media.id)
        assert error.value.status_code == 404


@pytest.mark.asyncio
async def test_untrusted_identity_and_conversation_access_are_rejected():
    org, conversation = uuid4(), uuid4()
    denied = Principal(org, uuid4(), uuid4(), uuid4(), frozenset())
    service = MediaService(FakePrivateStorage())
    with pytest.raises(HTTPException, match="conversation"):
        await service.initiate(
            denied,
            UploadRequest(
                conversation_id=conversation,
                filename="x.jpg",
                mime_type="image/jpeg",
                size_bytes=1,
                media_type="image",
            ),
        )


def test_client_cannot_supply_bucket_object_key_or_identity_fields():
    with pytest.raises(Exception):
        UploadRequest(
            conversation_id=uuid4(),
            filename="x.jpg",
            mime_type="image/jpeg",
            size_bytes=1,
            media_type="image",
            bucket="attacker-bucket",
            object_key="attacker-key",
            organization_id=uuid4(),
        )


@pytest.mark.asyncio
async def test_identity_issued_rs256_token_derives_media_principal(identity_token_factory):
    token, claims = identity_token_factory()

    assert await get_principal(f"Bearer {token}") == Principal(
        UUID(claims["org"]), UUID(claims["sub"]), UUID(claims["mid"]), UUID(claims["did"])
    )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "overrides",
    [
        {"exp": datetime.now(UTC) - timedelta(seconds=1)},
        {"iss": "wrong-issuer"},
        {"aud": "wrong-audience"},
        {"sub": None},
        {"org": None},
    ],
)
async def test_invalid_identity_token_claims_are_rejected(identity_token_factory, overrides):
    token, _ = identity_token_factory(**overrides)

    with pytest.raises(HTTPException, match="invalid"):
        await get_principal(f"Bearer {token}")


@pytest.mark.asyncio
async def test_legacy_hs256_and_unsigned_tokens_are_rejected(identity_token_factory):
    identity_token_factory()
    legacy = jwt.encode(
        {"sub": str(uuid4())}, "legacy-secret-at-least-thirty-two-bytes", algorithm="HS256"
    )
    unsigned = jwt.encode({"sub": str(uuid4())}, key="", algorithm="none")

    for token in (legacy, unsigned, "malformed"):
        with pytest.raises(HTTPException, match="invalid"):
            await get_principal(f"Bearer {token}")


@pytest.mark.asyncio
async def test_missing_bearer_token_and_untrusted_headers_are_rejected(identity_token_factory):
    identity_token_factory()

    with pytest.raises(HTTPException, match="authentication"):
        await get_principal(None)


def test_identity_headers_cannot_impersonate_a_principal():
    with TestClient(app) as client:
        response = client.post(
            "/api/v1/media/uploads",
            headers={
                "X-Organization-ID": str(uuid4()),
                "X-User-ID": str(uuid4()),
                "X-Member-ID": str(uuid4()),
            },
            json={
                "conversation_id": str(uuid4()),
                "filename": "x.jpg",
                "mime_type": "image/jpeg",
                "size_bytes": 1,
                "media_type": "image",
            },
        )

    assert response.status_code == 401
