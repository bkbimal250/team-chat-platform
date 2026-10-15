"""One local-only personal account smoke test; never prints credentials/tokens."""

import json
import secrets
import urllib.error
import urllib.request
from uuid import uuid4

from scripts.local import dev


def request(path, *, payload=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    req = urllib.request.Request(
        "http://127.0.0.1:8008" + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method or ("POST" if payload is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else None
    except urllib.error.HTTPError as error:
        # Avoid printing response bodies or request arguments.
        return error.code, None


def main():
    environment = dev.env("identity")
    if (
        environment.get("APP_ENV") != "development"
        or environment.get("OTP_PROVIDER") != "development"
    ):
        raise RuntimeError("This smoke test requires the isolated local development runner.")
    suffix = uuid4().hex
    payload = {
        "display_name": "Local Personal Smoke",
        "email": "personal-smoke-" + suffix + "@example.test",
        # Reserved North American fiction range; no provider is called.
        "phone": "+120255501" + str(secrets.randbelow(100)).zfill(2),
        "password": secrets.token_urlsafe(24),
        "device": {"installation_id": suffix, "platform": "WEB", "device_name": "Local smoke"},
    }
    status, tokens = request("/api/v1/auth/registration/personal", payload=payload)
    assert status == 201, "Local personal registration status: " + str(status)
    assert tokens["organization_id"] is None and tokens["member_id"] is None
    token = tokens["access_token"]
    status, me = request("/api/v1/auth/me", token=token)
    assert status == 200 and me["context"] == {"organization_id": None, "member_id": None}
    assert not me["identity"]["phone_verified"] and not me["identity"]["email_verified"]
    status, profile = request("/api/v1/users/me", token=token)
    assert status == 200 and profile["display_name"] == payload["display_name"]
    status, _ = request(
        "/api/v1/users/me/preferences",
        token=token,
        payload={"theme_preference": "dark"},
        method="PATCH",
    )
    assert status == 200
    status, preferences = request("/api/v1/users/me/preferences", token=token)
    assert status == 200 and preferences["theme_preference"] == "dark"
    assert request("/api/v1/users/me/privacy", token=token)[0] == 200
    status, devices = request("/api/v1/devices", token=token)
    assert status == 200 and len(devices) == 1
    assert request("/api/v1/users/search?q=Local", token=token)[0] == 403
    assert request("/api/v1/platform/me", token=token)[0] == 403
    assert request("/api/v1/conversations", token=token)[0] in {401, 403}
    login = {key: payload[key] for key in ("email", "password", "device")}
    status, tokens = request("/api/v1/auth/login", payload=login)
    assert status == 200 and tokens["organization_id"] is None
    status, tokens = request(
        "/api/v1/auth/refresh", payload={"refresh_token": tokens["refresh_token"]}
    )
    assert status == 200 and tokens["member_id"] is None
    assert request("/api/v1/auth/logout", token=tokens["access_token"], payload={})[0] == 200
    assert request("/api/v1/auth/me", token=tokens["access_token"])[0] == 401
    # Also close the original registration session.
    assert request("/api/v1/auth/logout", token=token, payload={})[0] == 200
    print("Personal registration/profile/preferences/privacy/devices/login/refresh/logout: PASS")
    print("Tenant directory/company chat/platform access denied: PASS")
    print("Real email/SMS: NO")


if __name__ == "__main__":
    main()
