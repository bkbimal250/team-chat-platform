import pytest

import app.main as main


class ReadyRedis:
    async def ping(self):
        return True

    async def aclose(self):
        return None


class UnavailableRedis(ReadyRedis):
    async def ping(self):
        raise RuntimeError("redis unavailable")


def test_health_routes_are_public():
    health_routes = {
        route.path: route for route in main.app.routes if route.path.startswith("/health/")
    }

    assert health_routes["/health/live"].dependencies == []
    assert health_routes["/health/ready"].dependencies == []


@pytest.mark.asyncio
async def test_live_and_ready_health_endpoints(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://example/0")
    monkeypatch.setattr(main.Redis, "from_url", lambda _: ReadyRedis())

    assert await main.live() == {"status": "alive"}
    assert await main.ready() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_returns_503_when_redis_is_unavailable(monkeypatch):
    monkeypatch.setenv("REDIS_URL", "redis://example/0")
    monkeypatch.setattr(main.Redis, "from_url", lambda _: UnavailableRedis())

    assert (await main.ready()).status_code == 503
