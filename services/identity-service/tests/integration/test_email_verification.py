# ruff: noqa: F401, F811

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.main import app
from app.models.models import EmailVerificationChallenge, Identity
from app.security.hashing import token_hash

from .test_email_password import (
    body,
    harness,
)


async def register(client):
    payload = body()
    response = await client.post("/api/v1/auth/registration/company", json=payload)
    assert response.status_code == 201
    return payload, response.json()


@pytest.mark.asyncio
async def test_registration_is_unverified_then_verification_is_single_use(harness, caplog):
    client, factory, _ = harness
    payload, tokens = await register(client)
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        assert identity.email_verified is False
        assert identity.email_verified_at is None

    # Login remains allowed while verification is an explicit, independent state.
    login = await client.post(
        "/api/v1/auth/login",
        json={key: payload[key] for key in ("email", "password", "device")},
    )
    assert login.status_code == 200
    resend = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": payload["email"]}
    )
    assert resend.status_code == 200
    raw_token = resend.json()["development_verification_token"]
    assert raw_token not in caplog.text
    verified = await client.post("/api/v1/auth/email/verify", json={"token": raw_token})
    assert verified.status_code == 204
    assert (await client.post("/api/v1/auth/email/verify", json={"token": raw_token})).json()[
        "error"
    ]["code"] == "EMAIL_VERIFICATION_INVALID"
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        assert identity.email_verified is True
        assert identity.email_verified_at is not None
        row = await db.scalar(
            select(EmailVerificationChallenge).where(
                EmailVerificationChallenge.token_hash == token_hash(raw_token)
            )
        )
        assert row is not None and row.consumed_at is not None
        assert raw_token != row.token_hash
    assert tokens["access_token"]


@pytest.mark.asyncio
async def test_resend_is_generic_rotates_tokens_and_enforces_limits(harness):
    client, factory, _ = harness
    payload, _ = await register(client)
    first = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": payload["email"]}
    )
    unknown = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": uuid4().hex + "@example.test"}
    )
    assert first.status_code == unknown.status_code == 200
    assert (
        set(first.json())
        == set(unknown.json())
        == {
            "message",
            "development_verification_token",
        }
    )
    second = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": payload["email"]}
    )
    assert second.status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/email/verify",
            json={"token": first.json()["development_verification_token"]},
        )
    ).json()["error"]["code"] == "EMAIL_VERIFICATION_INVALID"
    assert (
        await client.post(
            "/api/v1/auth/email/verify",
            json={"token": second.json()["development_verification_token"]},
        )
    ).status_code == 204
    digest = hashlib.sha256(payload["email"].encode()).hexdigest()
    app.state.redis.counts[f"password:email-verification:email:{digest}"] = 10
    limited = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": payload["email"]}
    )
    assert limited.status_code == 429
    async with factory() as db:
        rows = (
            await db.scalars(
                select(EmailVerificationChallenge).where(
                    EmailVerificationChallenge.identity_id
                    == (
                        await db.scalar(
                            select(Identity.id).where(Identity.email == payload["email"])
                        )
                    )
                )
            )
        ).all()
        assert all(row.token_hash != first.json()["development_verification_token"] for row in rows)


@pytest.mark.asyncio
async def test_invalid_expired_and_password_reset_are_separate(harness):
    client, factory, _ = harness
    payload, _ = await register(client)
    resend = await client.post(
        "/api/v1/auth/email/verification/resend", json={"email": payload["email"]}
    )
    raw_token = resend.json()["development_verification_token"]
    async with factory.begin() as db:
        row = await db.scalar(
            select(EmailVerificationChallenge).where(
                EmailVerificationChallenge.token_hash == token_hash(raw_token)
            )
        )
        row.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    expired = await client.post("/api/v1/auth/email/verify", json={"token": raw_token})
    invalid = await client.post("/api/v1/auth/email/verify", json={"token": "a" * 64})
    assert (
        expired.json()["error"]["code"]
        == invalid.json()["error"]["code"]
        == "EMAIL_VERIFICATION_INVALID"
    )
    reset = await client.post("/api/v1/auth/password/forgot", json={"email": payload["email"]})
    assert reset.status_code == 200
    async with factory() as db:
        identity = await db.scalar(select(Identity).where(Identity.email == payload["email"]))
        assert identity.email_verified is False
