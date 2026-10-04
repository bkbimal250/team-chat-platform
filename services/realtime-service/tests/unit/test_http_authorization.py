from types import SimpleNamespace
from uuid import uuid4

import httpx
import pytest

from app import authorization
from app.auth import Principal
from app.core import ProtocolError


@pytest.mark.parametrize("failure", [None, "denied", "tenant", "network"])
async def test_real_authorization_contract(monkeypatch, failure):
    principal = Principal(*[uuid4() for _ in range(5)])
    cid = uuid4()
    monkeypatch.setattr(
        authorization,
        "settings",
        lambda: SimpleNamespace(
            conversation_service_url="http://conversation", internal_service_token="internal"
        ),
    )

    async def handle(request):
        assert request.headers["X-Internal-Service-Token"] == "internal"
        assert request.url.path == f"/internal/v1/conversations/{cid}/authorize"
        if failure == "network":
            raise httpx.ConnectError("unavailable", request=request)
        return httpx.Response(
            200,
            json={
                "allowed": failure != "denied",
                "organization_id": str(
                    uuid4() if failure == "tenant" else principal.organization_id
                ),
                "member_id": str(principal.member_id),
                "conversation_id": str(cid),
            },
        )

    client = httpx.AsyncClient
    monkeypatch.setattr(
        authorization.httpx,
        "AsyncClient",
        lambda **kwargs: client(transport=httpx.MockTransport(handle), **kwargs),
    )
    if failure:
        with pytest.raises(ProtocolError):
            await authorization.ConversationAuthorizer().authorize(principal, cid)
    else:
        await authorization.ConversationAuthorizer().authorize(principal, cid)
