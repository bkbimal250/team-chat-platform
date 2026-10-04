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


def test_block_event_identifies_both_users_and_membership_identities():
    user = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")
    target = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Bob", status="ACTIVE")
    client, session = client_for(user)
    calls = 0

    async def scalar(*_):
        nonlocal calls
        calls += 1
        return user if calls == 1 else None

    async def get(*_):
        return target

    session.scalar = scalar
    session.get = get
    try:
        assert client.post(f"/api/v1/users/{target.id}/block").status_code == 200
        event = next(
            item for item in session.added if getattr(item, "event_type", "") == "user.blocked.v1"
        )
        assert event.payload["blocker_user_id"] == str(user.id)
        assert event.payload["blocked_user_id"] == str(target.id)
        assert event.payload["blocker_identity_id"] == str(user.identity_id)
        assert event.payload["blocked_identity_id"] == str(target.identity_id)
    finally:
        app.dependency_overrides.clear()


def test_unblock_event_retains_both_parties():
    user = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Ada", status="ACTIVE")
    target = User(id=uuid.uuid4(), identity_id=uuid.uuid4(), display_name="Bob", status="ACTIVE")
    client, session = client_for(user)

    async def get(*_):
        return target

    async def delete(*_):
        return None

    session.get = get
    session.delete = delete
    try:
        assert client.delete(f"/api/v1/users/{target.id}/block").status_code == 200
        event = next(
            item for item in session.added if getattr(item, "event_type", "") == "user.unblocked.v1"
        )
        assert event.payload["blocked_identity_id"] == str(target.identity_id)
        assert event.payload["blocker_identity_id"] == str(user.identity_id)
    finally:
        app.dependency_overrides.clear()
