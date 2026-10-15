import asyncio
import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import httpx
import jwt
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import Base, app, db


def test_personal_self_profile_preferences_privacy_and_directory_denial(monkeypatch):
    asyncio.run(exercise(monkeypatch))


async def exercise(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def dependency():
        async with factory() as session:
            yield session

    app.dependency_overrides[db] = dependency
    monkeypatch.setenv("INTERNAL_SERVICE_TOKEN", "personal-test-internal")
    identity_id, other_id = uuid4(), uuid4()
    now = datetime.now(UTC)
    claims = {
        "sub": str(identity_id),
        "sid": str(uuid4()),
        "did": str(uuid4()),
        "iss": "identity-service",
        "aud": "team-chat-platform",
        "iat": now,
        "exp": now + timedelta(minutes=5),
    }
    token = jwt.encode(claims, os.environ["ACCESS_TOKEN_PRIVATE_KEY"], algorithm="RS256")
    headers = {"Authorization": "Bearer " + token}
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            for identity in (identity_id, other_id):
                response = await client.post(
                    "/internal/v1/users/provision",
                    headers={"X-Internal-Service-Token": "personal-test-internal"},
                    json={"identity_id": str(identity), "display_name": "Personal user"},
                )
                assert response.status_code == 200
            assert (await client.get("/api/v1/users/me", headers=headers)).status_code == 200
            assert (
                await client.patch(
                    "/api/v1/users/me",
                    headers=headers,
                    json={"display_name": "Updated personal user"},
                )
            ).status_code == 200
            assert (await client.get("/api/v1/users/me", headers=headers)).json()[
                "display_name"
            ] == "Updated personal user"
            assert (
                await client.patch(
                    "/api/v1/users/me/preferences",
                    headers=headers,
                    json={"theme_preference": "dark"},
                )
            ).status_code == 200
            assert (await client.get("/api/v1/users/me/preferences", headers=headers)).json()[
                "theme_preference"
            ] == "dark"
            assert (
                await client.patch(
                    "/api/v1/users/me/privacy",
                    headers=headers,
                    json={"read_receipts_enabled": False},
                )
            ).status_code == 200
            assert (await client.get("/api/v1/users/me/privacy", headers=headers)).json()[
                "read_receipts_enabled"
            ] is False
            assert (
                await client.get("/api/v1/users/search?q=Personal", headers=headers)
            ).status_code == 403
            assert (
                await client.get(f"/api/v1/users/{other_id}", headers=headers)
            ).status_code == 404
            partial = jwt.encode(
                {**claims, "org": str(uuid4())},
                os.environ["ACCESS_TOKEN_PRIVATE_KEY"],
                algorithm="RS256",
            )
            assert (
                await client.get("/api/v1/users/me", headers={"Authorization": "Bearer " + partial})
            ).status_code == 401
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
