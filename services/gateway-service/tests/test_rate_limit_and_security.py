import httpx

from app.config import Settings
from app.main import create_app
from app.rate_limit import MemoryRateLimitStore


async def request(app, method: str, path: str, **kwargs) -> httpx.Response:
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="https://api.michat.in"
        ) as client:
            return await client.request(method, path, **kwargs)


async def test_auth_rate_limit_blocks_after_threshold():
    settings = Settings(
        organization_url="http://organization.test",
        identity_url="http://identity.test",
        user_url="http://user.test",
        conversation_url="http://conversation.test",
        messaging_url="http://messaging.test",
        media_url="http://media.test",
        notification_url="http://notification.test",
        rate_limit_enabled=True,
        rate_limit_auth_per_minute=1,
    )
    store = MemoryRateLimitStore()
    transport = httpx.MockTransport(
        lambda request: httpx.Response(201, json={"ok": True})
    )
    app = create_app(settings, transport, rate_limit_store=store)
    first = await request(app, "POST", "/api/v1/auth/login", json={"email": "a@b.test"})
    second = await request(app, "POST", "/api/v1/auth/login", json={"email": "a@b.test"})
    assert first.status_code == 201
    assert second.status_code == 429
    assert second.headers.get("retry-after")


async def test_rate_limit_store_errors_fail_open():
    class BrokenStore:
        async def consume(self, key, limit, window_seconds):
            raise RuntimeError("redis down")

    settings = Settings(
        organization_url="http://organization.test",
        identity_url="http://identity.test",
        user_url="http://user.test",
        conversation_url="http://conversation.test",
        messaging_url="http://messaging.test",
        media_url="http://media.test",
        notification_url="http://notification.test",
        rate_limit_enabled=True,
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"ok": True})
    )
    app = create_app(settings, transport, rate_limit_store=BrokenStore())
    response = await request(app, "GET", "/api/v1/users/me")
    assert response.status_code == 200


async def test_downstream_429_is_preserved():
    settings = Settings(
        organization_url="http://organization.test",
        identity_url="http://identity.test",
        user_url="http://user.test",
        conversation_url="http://conversation.test",
        messaging_url="http://messaging.test",
        media_url="http://media.test",
        notification_url="http://notification.test",
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(429, json={"detail": "limited"}, headers={"retry-after": "9"})
    )
    app = create_app(settings, transport)
    response = await request(app, "POST", "/api/v1/auth/otp/request", json={"phone": "+10000000000"})
    assert response.status_code == 429
    assert response.json()["detail"] == "limited"
    assert response.headers.get("retry-after") == "9"


async def test_security_headers_on_api_response():
    settings = Settings(
        app_env="production",
        organization_url="http://organization.internal:8000",
        identity_url="http://identity.internal:8001",
        user_url="http://user.internal:8002",
        conversation_url="http://conversation.internal:8003",
        messaging_url="http://messaging.internal:8004",
        media_url="http://media.internal:8005",
        notification_url="http://notification.internal:8006",
        realtime_url="http://realtime.internal:8007",
        redis_url="redis://redis.internal:6379/0",
        realtime_public_wss_url="wss://ws.michat.in/api/v1/realtime",
        rate_limit_enabled=False,
    )
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"ok": True})
    )
    app = create_app(settings, transport)
    response = await request(app, "GET", "/api/v1/users/me")
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert "frame-ancestors" in response.headers.get("content-security-policy", "")
    assert response.headers.get("strict-transport-security")
