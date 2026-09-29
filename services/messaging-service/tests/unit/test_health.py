import pytest

import app.main as main


class ReadySession:
    async def execute(self, _):
        return None

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


class UnavailableSession(ReadySession):
    async def execute(self, _):
        raise RuntimeError("database unavailable")


def test_health_routes_are_public():
    health_routes = {
        route.path: route for route in main.app.routes if route.path.startswith("/health/")
    }

    assert health_routes["/health/live"].dependencies == []
    assert health_routes["/health/ready"].dependencies == []


@pytest.mark.asyncio
async def test_live_and_ready_health_endpoints(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", lambda: ReadySession())

    assert await main.live() == {"status": "alive"}
    assert await main.ready() == {"status": "ready"}


@pytest.mark.asyncio
async def test_ready_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(main, "SessionLocal", lambda: UnavailableSession())

    assert (await main.ready()).status_code == 503
