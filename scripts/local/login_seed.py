"""Authenticate only the two explicitly seeded local users; print no credentials."""

import json

from smoke import LOCAL, call

sessions = []
for index in [1, 2]:
    status, challenge = call(
        "/api/v1/auth/otp/request",
        {"phone_number": f"+91900000000{index}", "purpose": "LOGIN"},
    )
    if status != 202 or not challenge.get("development_code"):
        code = challenge.get("error", {}).get("code", "not_issued")
        raise SystemExit(
            f"Local development OTP unavailable (HTTP {status}, {code}); "
            "no external provider attempted"
        )
    status, tokens = call(
        "/api/v1/auth/otp/verify",
        {
            "challenge_id": challenge["challenge_id"],
            "code": challenge["development_code"],
            "device": {
                "installation_id": f"globalchat-local-device-{index}",
                "platform": "WEB",
                "device_name": f"Local browser {index}",
            },
        },
    )
    if status != 200:
        raise SystemExit("Local verification failed")
    sessions.append(tokens)
(LOCAL / "sessions.json").write_text(json.dumps(sessions))
print("Two real local sessions obtained; tokens stored only in ignored .local/")
