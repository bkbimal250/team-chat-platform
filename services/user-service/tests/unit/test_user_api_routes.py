"""HTTP route tests with a fake async session; no database is opened."""

import uuid

from fastapi.testclient import TestClient

from app.auth import AuthContext, require_authenticated_context
from app.main import User, app, db


class Session:
    def __init__(self, user):
        self.user = user
        self.added = []

    async def scalar(self, *_):
        return self.user

    async def get(self, model, *_):
        if model.__name__ == "User":
            return self.user
        return None

    def add(self, value):
        self.added.append(value)

    def begin(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False


def client_for(user):
    context = AuthContext(user.identity_id, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), uuid.uuid4())
    session = Session(user)

    async def fake_db():
        yield session

    app.dependency_overrides[require_authenticated_context] = lambda: context
    app.dependency_overrides[db] = fake_db
    return TestClient(app), session


def test_get_me():
    user = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")
    client, _ = client_for(user)
    assert client.get("/api/v1/users/me").json()["display_name"] == "Ada"
    app.dependency_overrides.clear()


def test_patch_me_creates_profile_event():
    user = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")
    client, session = client_for(user)
    response = client.patch("/api/v1/users/me", json={"display_name": "Grace"})
    assert response.status_code == 200 and user.display_name == "Grace"
    assert any(
        getattr(item, "event_type", "") == "user.profile_updated.v1" for item in session.added
    )
    app.dependency_overrides.clear()


def test_self_block_is_rejected():
    user = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")
    client, _ = client_for(user)
    assert client.post(f"/api/v1/users/{user.id}/block").status_code == 422
    app.dependency_overrides.clear()
