from fastapi.testclient import TestClient

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


def test_live_and_ready_health_endpoints(monkeypatch):
    monkeypatch.setattr(main, "sessions", lambda: ReadySession())
    client = TestClient(main.app)

    assert client.get("/health/live").json() == {"status": "alive"}
    assert client.get("/health/ready").json() == {"status": "ready"}


def test_ready_returns_503_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(main, "sessions", lambda: UnavailableSession())

    assert TestClient(main.app).get("/health/ready").status_code == 503
