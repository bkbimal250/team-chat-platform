import json
from types import SimpleNamespace
from unittest.mock import Mock
from urllib.error import HTTPError, URLError
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.security import Principal, authorize_conversation


@pytest.mark.asyncio
async def test_production_authorization_uses_real_conversation_membership(monkeypatch):
    cid = uuid4()
    token = "Bearer synthetic-secret"
    identity = uuid4()
    p = Principal(None, identity, identity, uuid4(), authorization=token)
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.read.return_value = json.dumps(
        {
            "allowed": True,
            "conversation_id": str(cid),
            "organization_id": None,
            "member_id": str(p.member_id),
            "user_id": str(p.user_id),
        }
    ).encode()
    opener = Mock()
    opener.open.return_value = response
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: opener)
    monkeypatch.setattr(
        "app.security.get_settings",
        lambda: SimpleNamespace(
            conversation_api_url="http://conversation.globalchat.internal:8003",
            internal_service_token="service-secret",
        ),
    )
    await authorize_conversation(p, cid)
    request = opener.open.call_args.args[0]
    assert (
        request.full_url
        == f"http://conversation.globalchat.internal:8003/internal/v1/conversations/{cid}/authorize"
    )
    assert request.get_header("X-internal-service-token") == "service-secret"
    assert json.loads(request.data) == {
        "organization_id": None,
        "member_id": str(p.member_id),
        "identity_id": str(p.user_id),
    }
    assert token not in repr(p)


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", [403, 404, "network", "closed"])
async def test_conversation_authorization_fails_closed(monkeypatch, failure):
    cid = uuid4()
    p = Principal(uuid4(), uuid4(), uuid4(), uuid4(), authorization="Bearer synthetic")
    opener = Mock()
    if failure == "closed":
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.read.return_value = json.dumps({"id": str(cid), "status": "CLOSED"}).encode()
        opener.open.return_value = response
    else:
        opener.open.side_effect = (
            URLError("network")
            if failure == "network"
            else HTTPError("internal", failure, "denied", {}, None)
        )
    monkeypatch.setattr("urllib.request.build_opener", lambda *args: opener)
    monkeypatch.setattr(
        "app.security.get_settings",
        lambda: SimpleNamespace(
            conversation_api_url="http://conversation.globalchat.internal:8003",
            internal_service_token="service-secret",
        ),
    )
    with pytest.raises(HTTPException):
        await authorize_conversation(p, cid)


@pytest.mark.asyncio
@pytest.mark.parametrize("personal", [False, True])
async def test_only_uploader_can_mutate_but_participants_can_download(personal):
    from app.service import MediaRecord, MediaService
    from app.storage import FakePrivateStorage

    cid = uuid4()
    owner = Principal(None if personal else uuid4(), uuid4(), uuid4(), uuid4(), frozenset({cid}))
    peer = Principal(owner.organization_id, uuid4(), uuid4(), uuid4(), frozenset({cid}))
    record = MediaRecord(
        uuid4(),
        owner.organization_id,
        cid,
        owner.user_id,
        owner.member_id,
        owner.device_id,
        "audio",
        "audio/webm",
        "note.webm",
        "note.webm",
        100,
        None,
        "private",
        "key",
        status="READY",
    )
    service = MediaService(FakePrivateStorage())
    service.media[record.id] = record
    service.references.add((record.id, str(uuid4()), cid))
    record.reference_count = 1
    peer = Principal(owner.organization_id, peer.user_id, peer.member_id, peer.device_id, frozenset({cid}))
    assert await service._get_media(peer, record.id) == record
    with pytest.raises(HTTPException):
        await service._owned(peer, record.id)
