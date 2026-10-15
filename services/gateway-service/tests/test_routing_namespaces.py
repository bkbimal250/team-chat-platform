import pytest

from app.routing import normalize_path, owner_for


@pytest.mark.parametrize(
    "with_slash,without_slash,owner",
    [
        ("/api/v1/platform/organizations/", "/api/v1/platform/organizations", "organization"),
        (
            "/api/v1/platform/organizations/00000000-0000-0000-0000-000000000001/owners/",
            "/api/v1/platform/organizations/00000000-0000-0000-0000-000000000001/owners",
            "organization",
        ),
        ("/api/v1/invitations/", "/api/v1/invitations", "organization"),
        ("/api/v1/contacts/", "/api/v1/contacts", "user"),
    ],
)
def test_trailing_slash_normalization_matches(with_slash, without_slash, owner):
    assert owner_for(with_slash) == owner
    assert owner_for(without_slash) == owner
    assert normalize_path(with_slash) == normalize_path(without_slash)


@pytest.mark.parametrize(
    "path,owner",
    [
        ("/api/v1/auth/registration/personal", "identity"),
        ("/api/v1/auth/login", "identity"),
        ("/api/v1/auth/password/forgot", "identity"),
        ("/api/v1/auth/otp/request", "identity"),
        ("/api/v1/devices", "identity"),
        ("/api/v1/users/me/preferences", "user"),
        ("/api/v1/contacts/match", "user"),
        ("/api/v1/conversations/direct", "conversation"),
        ("/api/v1/conversations/c-1/messages", "messaging"),
        ("/api/v1/messages/m-1", "messaging"),
        ("/api/v1/media/uploads", "media"),
        ("/api/v1/notifications/preferences", "notification"),
        ("/api/v1/organizations/current", "organization"),
        ("/api/v1/branches", "organization"),
        ("/api/v1/teams", "organization"),
        ("/api/v1/members", "organization"),
        ("/api/v1/roles", "organization"),
        ("/api/v1/permissions", "organization"),
        ("/api/v1/role-assignments", "organization"),
        ("/api/v1/audit-logs", "organization"),
        ("/api/v1/platform/me", "identity"),
    ],
)
def test_personal_and_company_namespaces(path, owner):
    assert owner_for(path) == owner
