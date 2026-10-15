"""Real PostgreSQL contact ownership and privacy; Identity boundary is explicitly faked."""

import asyncio
import hashlib
import importlib
import os
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import jwt
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.main import Base, Contact, User, UserBlock, UserPrivacySettings, app, db

contacts = importlib.import_module("app.contacts")


@asynccontextmanager
async def harness(monkeypatch):
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    a, b, c = uuid4(), uuid4(), uuid4()
    async with factory.begin() as s:
        for identity, name in ((a, "Requester"), (b, "Actual profile"), (c, "Other owner")):
            s.add(User(id=identity, identity_id=identity, display_name=name, status="ACTIVE"))
            s.add(UserPrivacySettings(user_id=identity, discoverable=True))

    async def dependency():
        async with factory() as session:
            yield session

    app.dependency_overrides[db] = dependency
    digest = hashlib.sha256(str(b).encode()).hexdigest()
    unknown = hashlib.sha256(str(a).encode()).hexdigest()

    async def lookup(request, body):
        if "phones" in body:
            if any(p["phone"] == "invalid" for p in body["phones"]):
                from fastapi import HTTPException

                raise HTTPException(422, "Invalid complete phone")
            ds = [digest if p["phone"] == "+12025550123" else unknown for p in body["phones"]]
        else:
            ds = body["digests"]
        return [
            {"digest": d, "identity_id": str(b) if d == digest else None, "phone_verified": False}
            for d in ds
        ]

    monkeypatch.setattr(contacts, "identity_lookup", lookup)
    limiter = AsyncMock()
    monkeypatch.setattr(contacts, "rate_limit", limiter)

    def headers(identity, tenant=False):
        now = datetime.now(UTC)
        claims = {
            "sub": str(identity),
            "sid": str(uuid4()),
            "did": str(uuid4()),
            "iss": "identity-service",
            "aud": "team-chat-platform",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        if tenant:
            claims.update(org=str(uuid4()), mid=str(uuid4()))
        return {
            "Authorization": "Bearer "
            + jwt.encode(claims, os.environ["ACCESS_TOKEN_PRIVATE_KEY"], algorithm="RS256")
        }

    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            yield SimpleNamespace(
                client=client,
                factory=factory,
                a=a,
                b=b,
                c=c,
                digest=digest,
                headers=headers,
                limiter=limiter,
            )
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()


def test_contact_crud_private_labels_and_phone_replacement(monkeypatch):
    async def run():
        async with harness(monkeypatch) as h:
            hdr = h.headers(h.a)
            response = await h.client.post(
                "/api/v1/contacts",
                headers=hdr,
                json={
                    "phone": "+12025550123",
                    "given_name": "Office",
                    "family_name": "friend",
                    "phone_display": "+1 202-555-0123",
                },
            )
            assert response.status_code == 200, response.text
            item = response.json()
            cid = item["id"]
            assert item["local_label"] == "Office friend"
            assert item["given_name"] == "Office"
            assert item["family_name"] == "friend"
            assert item["phone_display"] == "+1 202-555-0123"
            assert item["matched_user"] == {
                "user_id": str(h.b),
                "display_name": "Actual profile",
                "avatar_media_id": None,
                "phone_verified": False,
            }
            assert "phone_digest" not in item and "phone" not in item
            assert (await h.client.get("/api/v1/contacts", headers=hdr)).json()["items"] == [item]
            updated = await h.client.patch(
                "/api/v1/contacts/" + cid,
                headers=hdr,
                json={"local_label": "Private rename", "phone": "+12025550124"},
            )
            assert updated.json()["matched_user"] is None
            async with h.factory() as s:
                assert (await s.get(User, h.b)).display_name == "Actual profile"
                stored = await s.scalar(select(Contact).where(Contact.id == cid))
                assert stored.phone_digest != h.digest
            assert (await h.client.delete("/api/v1/contacts/" + cid, headers=hdr)).json() == {
                "deleted": True
            }
            async with h.factory() as s:
                assert await s.get(User, h.b) is not None
            assert (await h.client.get("/api/v1/contacts", headers=hdr)).json()["items"] == []

    asyncio.run(run())


@pytest.mark.parametrize("method", ["GET", "PATCH", "DELETE"])
def test_other_owner_cannot_access_contact(monkeypatch, method):
    async def run():
        async with harness(monkeypatch) as h:
            item = (
                await h.client.post(
                    "/api/v1/contacts",
                    headers=h.headers(h.a),
                    json={"phone": "+12025550123", "local_label": "Private"},
                )
            ).json()
            response = await h.client.request(
                method,
                "/api/v1/contacts/" + item["id"],
                headers=h.headers(h.c),
                **({"json": {"local_label": "Stolen"}} if method == "PATCH" else {}),
            )
            assert response.status_code == 404
            assert "Private" not in response.text
            assert (await h.client.get("/api/v1/contacts", headers=h.headers(h.c))).json()[
                "items"
            ] == []

    asyncio.run(run())


@pytest.mark.parametrize(
    "policy", ["hidden", "blocked_by_requester", "blocked_by_target", "inactive", "deleted"]
)
def test_fresh_reads_suppress_privacy_changes_with_unknown_equivalent(monkeypatch, policy):
    async def run():
        async with harness(monkeypatch) as h:
            hdr = h.headers(h.a)
            item = (
                await h.client.post("/api/v1/contacts", headers=hdr, json={"phone": "+12025550123"})
            ).json()
            assert item["matched_user"]
            async with h.factory.begin() as s:
                if policy == "hidden":
                    (await s.get(UserPrivacySettings, h.b)).discoverable = False
                elif policy.startswith("blocked"):
                    s.add(
                        UserBlock(
                            blocker_user_id=h.a if policy == "blocked_by_requester" else h.b,
                            blocked_user_id=h.b if policy == "blocked_by_requester" else h.a,
                        )
                    )
                elif policy == "inactive":
                    (await s.get(User, h.b)).status = "DISABLED"
                else:
                    (await s.get(User, h.b)).deleted_at = datetime.now(UTC)
            response = (await h.client.get("/api/v1/contacts/" + item["id"], headers=hdr)).json()
            assert response["matched_user"] is None
            match = (
                await h.client.post(
                    "/api/v1/contacts/match",
                    headers=hdr,
                    json={"contacts": [{"phone": "+12025550123"}, {"phone": "+12025550124"}]},
                )
            ).json()
            assert [r["matched_user"] for r in match["results"]] == [None, None]
            assert str(h.b) not in str(response)

    asyncio.run(run())


def test_concurrent_add_is_unique_and_company_context_is_not_contact_owner(monkeypatch):
    async def run():
        async with harness(monkeypatch) as h:
            responses = await asyncio.gather(
                *[
                    h.client.post(
                        "/api/v1/contacts",
                        headers=h.headers(h.a, tenant=bool(i % 2)),
                        json={"phone": "+12025550123"},
                    )
                    for i in range(6)
                ]
            )
            assert all(r.status_code == 200 for r in responses)
            assert len({r.json()["id"] for r in responses}) == 1
            async with h.factory() as s:
                assert (
                    await s.scalar(
                        select(func.count())
                        .select_from(Contact)
                        .where(Contact.owner_user_id == h.a)
                    )
                    == 1
                )
            assert (await h.client.get("/api/v1/contacts", headers=h.headers(h.a, True))).json()[
                "items"
            ][0]["id"] == responses[0].json()["id"]

    asyncio.run(run())


def test_bounded_match_deduplicates_and_rejects_search_and_client_identity(monkeypatch):
    async def run():
        async with harness(monkeypatch) as h:
            hdr = h.headers(h.a)
            result = await h.client.post(
                "/api/v1/contacts/match",
                headers=hdr,
                json={"contacts": [{"phone": "+12025550123"}] * 2},
            )
            assert len(result.json()["results"]) == 1
            h.limiter.assert_awaited()
            for body in (
                {"contacts": [{"phone": "+12025550123"}] * 21},
                {"contacts": [{"phone": "+12025550123", "identity_id": str(h.b)}]},
                {"contacts": []},
            ):
                response = await h.client.post("/api/v1/contacts/match", headers=hdr, json=body)
                assert response.status_code == 422
                assert "+12025550123" not in response.text
            assert (await h.client.get("/api/v1/contacts?q=Actual", headers=hdr)).status_code == 422
            assert (
                await h.client.get("/api/v1/users/search?q=Actual", headers=hdr)
            ).status_code == 403
            assert (
                await h.client.post(
                    "/api/v1/contacts/match", json={"contacts": [{"phone": "+12025550123"}]}
                )
            ).status_code == 401

    asyncio.run(run())


@pytest.mark.parametrize(
    "visibility,expected",
    [("NOBODY", False), ("ORGANIZATION", False), ("CONTACTS", False), ("EVERYONE", True)],
)
def test_avatar_reference_obeys_privacy(monkeypatch, visibility, expected):
    async def run():
        async with harness(monkeypatch) as h:
            avatar = uuid4()
            async with h.factory.begin() as s:
                (await s.get(User, h.b)).avatar_media_id = avatar
                (await s.get(UserPrivacySettings, h.b)).profile_photo_visibility = visibility
            result = (
                await h.client.post(
                    "/api/v1/contacts/match",
                    headers=h.headers(h.a),
                    json={"contacts": [{"phone": "+12025550123"}]},
                )
            ).json()
            assert result["results"][0]["matched_user"]["avatar_media_id"] == (
                str(avatar) if expected else None
            )

    asyncio.run(run())


def test_database_failure_never_logs_contact_parameters(monkeypatch, caplog):
    from sqlalchemy.exc import SQLAlchemyError

    async def run():
        async with harness(monkeypatch) as h:
            private = "private-label-and-phone-should-not-be-logged"
            monkeypatch.setattr(contacts, "owner", AsyncMock(side_effect=SQLAlchemyError(private)))
            response = await h.client.get("/api/v1/contacts", headers=h.headers(h.a))
            assert response.status_code == 503
            assert private not in response.text and private not in caplog.text

    asyncio.run(run())


def test_personal_contact_authorization_rechecks_owner_privacy_and_block(monkeypatch):
    async def scenario():
        async with harness(monkeypatch) as h:
            saved = (
                await h.client.post(
                    "/api/v1/contacts", headers=h.headers(h.a), json={"phone": "+12025550123"}
                )
            ).json()
            headers = {"X-Internal-Service-Token": os.environ["INTERNAL_SERVICE_TOKEN"]}
            route = "/internal/v1/contacts/authorize"
            body = {"identity_id": str(h.a), "contact_id": saved["id"]}
            assert (await h.client.post(route, headers=headers, json=body)).status_code == 200
            assert (
                await h.client.post(route, headers=headers, json=body | {"identity_id": str(h.c)})
            ).status_code == 404
            assert (
                await h.client.post(route, headers=h.headers(h.a), json=body)
            ).status_code != 200
            async with h.factory.begin() as db:
                privacy = await db.get(UserPrivacySettings, h.b)
                privacy.discoverable = False
            assert (await h.client.post(route, headers=headers, json=body)).status_code == 404
            async with h.factory.begin() as db:
                (await db.get(UserPrivacySettings, h.b)).discoverable = True
                db.add(UserBlock(blocker_user_id=h.b, blocked_user_id=h.a))
            assert (await h.client.post(route, headers=headers, json=body)).status_code == 404
            allowed = await h.client.post(
                "/internal/v1/contacts/communication",
                headers=headers,
                json={"identity_id": str(h.a), "peer_identity_id": str(h.b)},
            )
            assert allowed.json() == {"allowed": False}

    asyncio.run(scenario())


@pytest.mark.parametrize("hours", [24, 3, None])
def test_profile_photo_duration_is_durable_and_owned(monkeypatch, hours):
    import app.profile_photos as photos

    async def scenario():
        async with harness(monkeypatch) as h:
            photo_id = uuid4()
            resolve = AsyncMock(return_value="https://private.invalid/photo")
            monkeypatch.setattr(photos, "resolve_photo", resolve)
            result = await h.client.put(
                "/api/v1/users/me/photo",
                headers=h.headers(h.a),
                json={"media_id": str(photo_id), "duration_hours": hours},
            )
            assert result.status_code == 200
            resolve.assert_awaited_once_with(photo_id, h.a)
            async with h.factory() as s:
                user = await s.get(User, h.a)
                assert user.avatar_media_id == photo_id
                if hours is None:
                    assert user.avatar_expires_at is None
                else:
                    seconds = (user.avatar_expires_at - datetime.now(UTC)).total_seconds()
                    assert hours * 3600 - 10 < seconds <= hours * 3600
            fresh = await h.client.get("/api/v1/users/me", headers=h.headers(h.a))
            assert fresh.json()["avatar_media_id"] == str(photo_id)
            assert (
                await h.client.get(
                    f"/api/v1/users/profile-photos/{photo_id}", headers=h.headers(h.b)
                )
            ).status_code == 404
            assert (
                await h.client.get(
                    f"/api/v1/users/profile-photos/{photo_id}", headers=h.headers(h.a)
                )
            ).status_code == 200
            if hours is not None:
                async with h.factory.begin() as s:
                    (await s.get(User, h.a)).avatar_expires_at = datetime.now(UTC) - timedelta(
                        seconds=1
                    )
                assert (await h.client.get("/api/v1/users/me", headers=h.headers(h.a))).json()[
                    "avatar_media_id"
                ] is None
                assert (
                    await h.client.get(
                        f"/api/v1/users/profile-photos/{photo_id}", headers=h.headers(h.a)
                    )
                ).status_code == 404
            removed = await h.client.delete("/api/v1/users/me/photo", headers=h.headers(h.a))
            assert removed.status_code == 200 and removed.json()["avatar_media_id"] is None

    asyncio.run(scenario())


def test_profile_photo_rejects_invalid_duration_and_legacy_bypass(monkeypatch):
    async def scenario():
        async with harness(monkeypatch) as h:
            for hours in (0, -1, 8761, 1.5, "24"):
                result = await h.client.put(
                    "/api/v1/users/me/photo",
                    headers=h.headers(h.a),
                    json={"media_id": str(uuid4()), "duration_hours": hours},
                )
                assert result.status_code == 422
            assert (
                await h.client.patch(
                    "/api/v1/users/me",
                    headers=h.headers(h.a),
                    json={"avatar_media_id": str(uuid4())},
                )
            ).status_code == 422

    asyncio.run(scenario())


def test_presence_privacy_and_mutual_block_are_authoritative(monkeypatch):
    async def scenario():
        async with harness(monkeypatch) as h:
            route = "/internal/v1/contacts/presence-permission"
            headers = {"X-Internal-Service-Token": os.environ["INTERNAL_SERVICE_TOKEN"]}
            body = {"identity_id": str(h.a), "target_identity_id": str(h.b)}
            assert (await h.client.post(route, json=body)).status_code in (401, 403)
            assert not (await h.client.post(route, headers=headers, json=body)).json()["allowed"]
            async with h.factory.begin() as s:
                (await s.get(UserPrivacySettings, h.b)).online_status_visibility = "EVERYONE"
            assert (await h.client.post(route, headers=headers, json=body)).json()["allowed"]
            async with h.factory.begin() as s:
                s.add(UserBlock(blocker_user_id=h.a, blocked_user_id=h.b))
            assert not (await h.client.post(route, headers=headers, json=body)).json()["allowed"]
            result = await h.client.patch(
                "/api/v1/users/me/privacy",
                headers=h.headers(h.a),
                json={"read_receipts_enabled": None},
            )
            assert result.status_code == 422

    asyncio.run(scenario())
