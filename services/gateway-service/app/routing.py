import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteOwner:
    name: str
    service: str
    pattern: re.Pattern[str]


# Specific messaging conversation subresources precede the conversation catch-all.
ROUTE_OWNERS = (
    RouteOwner(
        "messaging-conversation",
        "messaging",
        re.compile(r"^/api/v1/conversations/[^/]+/(?:messages(?:/.*)?|delivered|read)/?$"),
    ),
    RouteOwner("messaging-message", "messaging", re.compile(r"^/api/v1/messages(?:/.*)?$")),
    RouteOwner("identity-auth", "identity", re.compile(r"^/api/v1/auth(?:/.*)?$")),
    RouteOwner("identity-devices", "identity", re.compile(r"^/api/v1/devices(?:/.*)?$")),
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
    matches = [owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(path)]
    if not matches:
        return None
    return matches[0]


def collisions_for(paths: list[str]) -> dict[str, list[str]]:
    collisions: dict[str, list[str]] = {}
    for path in paths:
        services = {owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(path)}
        if len(services) > 1:
            collisions[path] = sorted(services)
    return collisions
