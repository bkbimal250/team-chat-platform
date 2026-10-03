import json

import httpx
import pytest

from app.config import Settings
from app.main import create_app
from app.routing import collisions_for, owner_for


@pytest.fixture
def requests_seen():
    return []


@pytest.fixture
def transport(requests_seen):
    async def handler(request: httpx.Request) -> httpx.Response:
        requests_seen.append(request)
        return httpx.Response(
            201,
            json={"forwarded": True},
            headers={"x-request-id": "upstream", "connection": "close"},
        )

    return httpx.MockTransport(handler)


@pytest.fixture
def settings():
    return Settings(
        organization_url="http://organization.test",
        identity_url="http://identity.test",
        user_url="http://user.test",
        conversation_url="http://conversation.test",
        messaging_url="http://messaging.test",
        media_url="http://media.test",
        notification_url="http://notification.test",
    )


async def request(app, method: str, path: str, **kwargs) -> httpx.Response:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://api.michat.in"
        ) as client:
            return await client.request(method, path, **kwargs)


def test_route_ownership_is_deterministic():
    expected = {
        "/api/v1/auth/me": "identity",
        "/api/v1/users/me": "user",
        "/api/v1/organizations/current": "organization",
        "/api/v1/conversations/c-1": "conversation",
        "/api/v1/conversations/c-1/messages": "messaging",
        "/api/v1/conversations/c-1/read": "messaging",
        "/api/v1/messages/m-1/reactions": "messaging",
        "/api/v1/media/m-1/download": "media",
        "/api/v1/notifications/preferences": "notification",
    }
    assert {path: owner_for(path) for path in expected} == expected


def test_route_collision_precedence_is_explicit():
    collisions = collisions_for(
        ["/api/v1/conversations/c-1/messages", "/api/v1/conversations/c-1/read"]
    )
    assert collisions == {
        "/api/v1/conversations/c-1/messages": ["conversation", "messaging"],
        "/api/v1/conversations/c-1/read": ["conversation", "messaging"],
    }
    assert owner_for("/api/v1/conversations/c-1/messages") == "messaging"


@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "PATCH", "DELETE"])
async def test_method_forwarding(method, settings, transport, requests_seen):
    response = await request(
        create_app(settings, transport), method, "/api/v1/notifications/preferences"
    )
    assert response.status_code == 201
    assert requests_seen[0].method == method


async def test_query_json_authorization_and_tenant_headers_forwarded(
    settings, transport, requests_seen
):
    response = await request(
        create_app(settings, transport),
        "PATCH",
        "/api/v1/users/me?include=preferences",
        json={"display_name": "A"},
        headers={
            "Authorization": "Bearer signed.jwt",
            "X-Correlation-ID": "corr-123",
            "Cookie": "private=ignored",
            "X-Organization-ID": "must-not-be-trusted",
        },
    )
    forwarded = requests_seen[0]
    assert response.status_code == 201
    assert forwarded.url.query == b"include=preferences"
    assert json.loads(forwarded.content) == {"display_name": "A"}
    assert forwarded.headers["authorization"] == "Bearer signed.jwt"
    assert forwarded.headers["x-correlation-id"] == "corr-123"
    assert "cookie" not in forwarded.headers
    assert "x-organization-id" not in forwarded.headers


async def test_gateway_preserves_forwarded_https_for_organization(
    settings, transport, requests_seen
):
    app = create_app(settings, transport)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://gateway.internal"
        ) as client:
            response = await client.get(
                "/api/v1/organizations/current",
                headers={"X-Forwarded-Proto": "https"},
            )

    assert response.status_code == 201
    assert requests_seen[0].headers["x-forwarded-proto"] == "https"


async def test_safe_header_filtering(settings, transport, requests_seen):
    response = await request(
        create_app(settings, transport),
        "GET",
        "/api/v1/users/me",
        headers={"Connection": "upgrade", "X-Internal-Token": "secret"},
    )
    assert "connection" not in response.headers
    assert requests_seen[0].headers.get("connection") != "upgrade"
    assert "x-internal-token" not in requests_seen[0].headers


async def test_downstream_status_and_body_propagate(settings):
    transport = httpx.MockTransport(
        lambda request: httpx.Response(422, json={"detail": "invalid input"})
    )
    response = await request(create_app(settings, transport), "POST", "/api/v1/auth/otp/request")
    assert response.status_code == 422
    assert response.json() == {"detail": "invalid input"}


async def test_unknown_and_internal_routes_are_not_exposed(settings, transport):
    app = create_app(settings, transport)
    assert (await request(app, "GET", "/api/v1/unknown")).status_code == 404
    assert (await request(app, "POST", "/internal/v1/users/projections")).status_code == 404


async def test_timeout_is_sanitized_and_does_not_leak_secrets(settings):
    async def fail(request):
        raise httpx.ReadTimeout("http://user.test?token=super-secret", request=request)

    response = await request(
        create_app(settings, httpx.MockTransport(fail)),
        "GET",
        "/api/v1/users/me",
        headers={"Authorization": "Bearer signed.jwt"},
    )
    assert response.status_code == 504
    assert "user.test" not in response.text
    assert "super-secret" not in response.text
    assert "signed.jwt" not in response.text


async def test_connection_failure_is_sanitized(settings):
    async def fail(request):
        raise httpx.ConnectError("private host failed", request=request)

    response = await request(
        create_app(settings, httpx.MockTransport(fail)), "GET", "/api/v1/users/me"
    )
    assert response.status_code == 502
    assert "private host" not in response.text


async def test_health_does_not_probe_downstreams(settings, transport, requests_seen):
    app = create_app(settings, transport)
    live = await request(app, "GET", "/health/live")
    ready = await request(app, "GET", "/health/ready")
    assert live.json() == {"status": "alive"}
    assert ready.json() == {"status": "ready"}
    assert requests_seen == []


async def test_media_signing_metadata_uses_media_without_proxying_s3(
    settings, transport, requests_seen
):
    response = await request(
        create_app(settings, transport),
        "POST",
        "/api/v1/media/uploads",
        json={"file_name": "photo.jpg", "size": 42},
    )
    assert response.status_code == 201
    assert requests_seen[0].url.host == "media.test"
    assert requests_seen[0].url.path == "/api/v1/media/uploads"


async def test_request_size_is_bounded(settings, transport, requests_seen):
    settings.max_request_bytes = 3
    response = await request(
        create_app(settings, transport), "POST", "/api/v1/media/uploads", content=b"1234"
    )
    assert response.status_code == 413
    assert requests_seen == []


async def test_cors_allows_only_production_origins(settings, transport):
    app = create_app(settings, transport)
    allowed = await request(
        app,
        "OPTIONS",
        "/api/v1/users/me",
        headers={
            "Origin": "https://admin.michat.in",
            "Access-Control-Request-Method": "GET",
        },
    )
    denied = await request(
        app,
        "OPTIONS",
        "/api/v1/users/me",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers["access-control-allow-origin"] == "https://admin.michat.in"
    assert "access-control-allow-origin" not in denied.headers
