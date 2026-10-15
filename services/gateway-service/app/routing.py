import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteOwner:
    name: str
    service: str
    pattern: re.Pattern[str]


def normalize_path(path: str) -> str:
    if not path:
        return "/"
    if not path.startswith("/"):
        path = f"/{path}"
    if len(path) > 1 and path.endswith("/"):
        path = path.rstrip("/")
    return path


# Specific messaging conversation subresources precede the conversation catch-all.
ROUTE_OWNERS = (
    RouteOwner(
        "platform-organizations",
        "organization",
        re.compile(
            r"^/api/v1/platform/(?:organizations(?:/[0-9a-fA-F-]{36}"
            r"(?:/(?:owners|memberships|invitations|security))?)?|"
            r"identities/[0-9a-fA-F-]{36}/memberships)$"
        ),
    ),
    RouteOwner(
        "platform-identity",
        "identity",
        re.compile(
            r"^/api/v1/platform/(?:me|admins|audit|sessions(?:/[0-9a-fA-F-]{36}/revoke)?|"
            r"identities(?:/[0-9a-fA-F-]{36}(?:/sessions/revoke)?)?)$"
        ),
    ),
    RouteOwner(
        "messaging-conversation",
        "messaging",
        re.compile(r"^/api/v1/conversations/[^/]+/(?:messages(?:/.*)?|delivered|read)$"),
    ),
    RouteOwner("messaging-message", "messaging", re.compile(r"^/api/v1/messages(?:/.*)?$")),
    RouteOwner("identity-auth", "identity", re.compile(r"^/api/v1/auth(?:/.*)?$")),
    RouteOwner(
        "identity-user-devices",
        "identity",
        re.compile(r"^/api/v1/users/[0-9a-fA-F-]{36}/devices$"),
    ),
    RouteOwner("identity-e2ee", "identity", re.compile(r"^/api/v1/e2ee(?:/.*)?$")),
    RouteOwner("identity-devices", "identity", re.compile(r"^/api/v1/devices(?:/.*)?$")),
    RouteOwner("contacts", "user", re.compile(r"^/api/v1/contacts(?:/.*)?$")),
    RouteOwner("user", "user", re.compile(r"^/api/v1/users(?:/.*)?$")),
    RouteOwner("conversation", "conversation", re.compile(r"^/api/v1/conversations(?:/.*)?$")),
    RouteOwner("media", "media", re.compile(r"^/api/v1/media(?:/.*)?$")),
    RouteOwner("notification", "notification", re.compile(r"^/api/v1/notifications(?:/.*)?$")),
    RouteOwner(
        "organization",
        "organization",
        re.compile(
            r"^/api/v1/(?:organizations|branches|teams|members|invitations|roles|"
            r"permissions|role-assignments|audit-logs)(?:/.*)?$"
        ),
    ),
)


def owner_for(path: str) -> str | None:
    normalized = normalize_path(path)
    matches = [owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(normalized)]
    if not matches:
        return None
    return matches[0]


def collisions_for(paths: list[str]) -> dict[str, list[str]]:
    collisions: dict[str, list[str]] = {}
    for path in paths:
        normalized = normalize_path(path)
        services = {
            owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(normalized)
        }
        if len(services) > 1:
            collisions[path] = sorted(services)
    return collisions
