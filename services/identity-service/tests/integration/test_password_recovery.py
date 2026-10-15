import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.main import app
from app.models.models import Identity, PasswordResetChallenge, Session, SessionStatus
from app.security.hashing import token_hash, verify_secret

from .test_email_password import harness as harness


def body():
    return {
        "company_name": "Recovery Company",
        "owner_name": "Recovery Owner",
        "email": uuid4().hex + "@example.test",
        "phone": "+9198" + str(uuid4().int % 100000000).zfill(8),
        "password": "A long password with spaces!",
        "device": {
            "installation_id": uuid4().hex,
            "platform": "WEB",
            "device_name": "Recovery test",
        },
    }


async def register(client):
    payload = body()
    response = await client.post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 201
    return payload, response.json()


@pytest.mark.asyncio
async def test_forgot_password_is_generic_for_known_and_unknown_accounts(harness, caplog):
    client, _, _ = harness
    payload, _ = await register(client)
    known = await client.post("/api/v1/auth/password/forgot", json={"email": payload["email"]})
    unknown = await client.post(
        "/api/v1/auth/password/forgot", json={"email": uuid4().hex + "@example.test"}
    )
    assert known.status_code == unknown.status_code == 200
    assert known.json()["message"] == unknown.json()["message"]
    assert set(known.json()) == set(unknown.json()) == {"message", "development_reset_token"}
    assert known.json()["development_reset_token"] not in caplog.text


@pytest.mark.asyncio
async def test_password_reset_changes_argon2_hash_revokes_sessions_and_is_single_use(harness):
    client, factory, _ = harness
    payload, tokens = await register(client)
    forgot = await client.post("/api/v1/auth/password/forgot", json={"email": payload["email"]})
    reset_token = forgot.json()["development_reset_token"]
    new_password = "A new long password 123!"
    response = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": reset_token, "new_password": new_password},
    )
    assert response.status_code == 204
    assert (
        await client.post(
            "/api/v1/auth/password/reset", json={"token": reset_token, "new_password": new_password}
        )
    ).json()["error"]["code"] == "PASSWORD_RESET_INVALID"
    old_login = await client.post(
        "/api/v1/auth/login",
        json={
            **{key: payload[key] for key in ("email", "device")},
            "password": payload["password"],
        },
    )
    new_login = await client.post(
        "/api/v1/auth/login",
        json={**{key: payload[key] for key in ("email", "device")}, "password": new_password},
    )
    assert old_login.status_code == 401
    assert new_login.status_code == 200
    assert (
        await client.post("/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
    ).status_code == 401
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        assert verify_secret(new_password, identity.password_hash)
        assert not verify_secret(payload["password"], identity.password_hash)
        sessions = (
            await db.scalars(select(Session).where(Session.identity_id == identity.id))
        ).all()
        assert any(session.status == SessionStatus.REVOKED for session in sessions)
        challenge = await db.scalar(
            select(PasswordResetChallenge).where(
                PasswordResetChallenge.token_hash == token_hash(reset_token)
            )
        )
        assert challenge.consumed_at is not None


@pytest.mark.asyncio
async def test_invalid_expired_weak_and_rate_limited_password_recovery(harness):
    client, factory, _ = harness
    payload, _ = await register(client)
    invalid = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": "a" * 64, "new_password": "A valid replacement password!"},
    )
    assert invalid.json()["error"]["code"] == "PASSWORD_RESET_INVALID"
    forgot = await client.post("/api/v1/auth/password/forgot", json={"email": payload["email"]})
    reset_token = forgot.json()["development_reset_token"]
    weak = await client.post(
        "/api/v1/auth/password/reset", json={"token": reset_token, "new_password": "short"}
    )
    assert weak.status_code == 422
    async with factory.begin() as db:
        row = await db.scalar(
            select(PasswordResetChallenge).where(
                PasswordResetChallenge.token_hash == token_hash(reset_token)
            )
        )
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    expired = await client.post(
        "/api/v1/auth/password/reset",
        json={"token": reset_token, "new_password": "A valid replacement password!"},
    )
    assert expired.json()["error"]["code"] == "PASSWORD_RESET_INVALID"
    digest = hashlib.sha256(payload["email"].encode()).hexdigest()
    app.state.redis.counts[f"password:password-reset:email:{digest}"] = 10
    assert (
        await client.post("/api/v1/auth/password/forgot", json={"email": payload["email"]})
    ).status_code == 429
