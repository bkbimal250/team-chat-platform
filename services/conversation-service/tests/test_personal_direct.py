"""Personal scope on PostgreSQL, including concurrent reverse creation."""

import asyncio
import os
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api import authorize_send, get_conversation
from app.core import DomainError
from app.models import ConversationMember
from app.services import ConversationService


@pytest.mark.asyncio
async def test_personal_creation_concurrent_reverse_and_authorization(monkeypatch):
    if "DATABASE_URL" not in os.environ:
        pytest.skip("DATABASE_URL required for PostgreSQL integration test")
    engine = create_async_engine(os.environ["DATABASE_URL"], poolclass=NullPool)
    sessions = async_sessionmaker(engine, expire_on_commit=False)
    a, b, c, contact = (uuid4() for _ in range(4))

    async def post(client, url, **kwargs):
        body = kwargs["json"]
        if url.endswith("/authorize"):
            assert body["contact_id"] == str(contact)
            target = b if body["identity_id"] == str(a) else a
            return httpx.Response(
                200, json={"identity_id": str(target)}, request=httpx.Request("POST", url)
            )
        return httpx.Response(200, json={"allowed": True}, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", post)

    async def not_blocked(*_):
        return False

    monkeypatch.setattr("app.services.blocked_between", not_blocked)

    async def create(actor):
        async with sessions.begin() as db:
            row, created = await ConversationService().personal_direct(db, actor, contact, "test")
            return row.id, created

    results = await asyncio.gather(*(create(actor) for actor in (a, b, a, b)))
    assert len({r[0] for r in results}) == 1
    assert sum(r[1] for r in results) == 1
    cid = results[0][0]
    async with sessions.begin() as db:
        assert (
            await db.scalar(
                select(func.count())
                .select_from(ConversationMember)
                .where(ConversationMember.conversation_id == cid)
            )
            == 2
        )
        assert (await get_conversation(cid, None, db)).organization_id is None
        for actor in (a, b):
            answer = await authorize_send(
                cid,
                {"organization_id": None, "member_id": str(actor), "identity_id": str(actor)},
                None,
                db,
            )
            assert answer["allowed"]
        answer = await authorize_send(
            cid, {"organization_id": None, "member_id": str(c), "identity_id": str(c)}, None, db
        )
        assert not answer["allowed"]
        with pytest.raises(DomainError):
            await get_conversation(cid, uuid4(), db)
        with pytest.raises(DomainError):
            await authorize_send(
                cid, {"organization_id": None, "member_id": str(a), "identity_id": str(c)}, None, db
            )
    await engine.dispose()


@pytest.mark.asyncio
async def test_personal_contact_rejection_does_not_create(monkeypatch):
    async def post(client, url, **kwargs):
        return httpx.Response(404, request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx.AsyncClient, "post", post)
    db = AsyncMock()
    with pytest.raises(DomainError) as error:
        await ConversationService().personal_direct(db, uuid4(), uuid4(), "test")
    assert error.value.code == "CONTACT_UNAVAILABLE"
    db.execute.assert_not_called()
