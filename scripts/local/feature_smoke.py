"""Exercise real local attachments, groups, settings, QR and security boundaries."""

import hashlib
import json
import time
import urllib.request
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from smoke import LOCAL, call, record, results


def main():
    results.update(json.loads((LOCAL / "smoke-results.json").read_text()))
    sessions = json.loads((LOCAL / "sessions.json").read_text())
    alice, bob = [s["access_token"] for s in sessions]
    cid = json.loads((LOCAL / "conversation.json").read_text())["id"]
    for name, mime, kind, message_type in [
        ("image.png", "image/png", "image", "IMAGE"),
        ("video.mp4", "video/mp4", "video", "VIDEO"),
        ("audio.wav", "audio/wav", "audio", "AUDIO"),
        ("voice.webm", "audio/webm", "audio", "VOICE"),
        ("document.pdf", "application/pdf", "document", "DOCUMENT"),
    ]:
        data = (LOCAL / "fixtures" / name).read_bytes()
        status, upload = call(
            "/api/v1/media/uploads",
            {
                "conversation_id": cid,
                "filename": name,
                "mime_type": mime,
                "size_bytes": len(data),
                "media_type": kind,
                "checksum_sha256": hashlib.sha256(data).hexdigest(),
            },
            alice,
        )
        record(kind + "_authorization_" + name, status == 201)
        request = urllib.request.Request(
            upload["upload_url"],
            data=data,
            method="PUT",
            headers=upload["required_headers"],
        )
        with urllib.request.urlopen(request) as response:
            record(name + "_byte_upload", response.status == 200)
        media_id = upload["media_id"]
        status, _ = call(f"/api/v1/media/{media_id}/complete", {}, alice)
        record(name + "_complete", status == 200)
        body = {
            "client_message_id": str(uuid4()),
            "type": message_type,
            "media_id": media_id,
        }
        for _ in range(20):
            status, _ = call(f"/api/v1/conversations/{cid}/messages", body, alice)
            if status in {200, 201}:
                break
            time.sleep(0.25)
        record(name + "_message", status in {200, 201})
        status, download = call(f"/api/v1/media/{media_id}/download", token=bob)
        record(name + "_recipient_access", status == 200)
        with urllib.request.urlopen(download["download_url"]) as response:
            record(name + "_download", response.read() == data)
    status, group = call(
        "/api/v1/conversations/groups",
        {"title": "Local integration group", "member_ids": [sessions[1]["member_id"]]},
        alice,
    )
    record("group_create", status == 201)
    gid, mid = group["id"], sessions[1]["member_id"]
    for action in ["promote", "demote"]:
        status, _ = call(
            f"/api/v1/conversations/{gid}/members/{mid}/{action}", {}, alice
        )
        record("group_" + action, status == 200)
    status, _ = call(
        f"/api/v1/conversations/{gid}/members/{mid}", token=alice, method="DELETE"
    )
    record("group_remove", status == 200)
    status, _ = call(
        f"/api/v1/conversations/{gid}/members", {"member_ids": [mid]}, alice
    )
    record("group_add", status == 200)
    status, _ = call(f"/api/v1/conversations/{gid}/leave", {}, bob)
    record("group_leave", status == 200)
    for path in [
        "/api/v1/users/me",
        "/api/v1/users/me/privacy",
        "/api/v1/notifications/preferences",
        "/api/v1/notifications",
        "/api/v1/devices",
    ]:
        status, _ = call(path, token=alice)
        record(path + "_read", status == 200)
    for path in [
        "/api/v1/users/me",
        f"/api/v1/conversations/{cid}/messages",
        f"/api/v1/conversations/{cid}",
    ]:
        status, _ = call(path)
        record(path + "_missing_token_denied", status in {401, 403, 422})
    status, _ = call(f"/api/v1/devices/{sessions[1]['device_id']}", token=alice)
    record("other_users_device_denied", status == 404)
    status, qr = call(
        "/api/v1/auth/qr/challenges",
        {
            "installation_id": "local-qr-" + str(uuid4()),
            "platform": "WEB",
            "device_name": "Local QR browser",
        },
    )
    record("qr_create", status == 201)
    secret = parse_qs(urlparse(qr["payload"]).query)["challenge"][0].split(".", 1)[1]
    qid = qr["challenge_id"]
    status, _ = call(
        f"/api/v1/auth/qr/challenges/{qid}/authorize", {"secret": secret}, alice
    )
    record("qr_authorize", status == 200)
    status, linked = call(
        f"/api/v1/auth/qr/challenges/{qid}/consume", {"secret": secret}
    )
    record("qr_consume", status == 200)
    status, _ = call(f"/api/v1/auth/qr/challenges/{qid}/consume", {"secret": secret})
    record("qr_single_use", status in {400, 409})
    # The public User UUID differs from the membership's Identity UUID.
    status, peer = call("/api/v1/users/me", token=bob)
    record("block_peer_lookup", status == 200)
    block_path = f"/api/v1/users/{peer['user_id']}/block"
    status, _ = call(block_path, {}, alice)
    record("block_public_api", status == 200)
    try:
        deadline = time.monotonic() + 20
        denied = False
        while time.monotonic() < deadline:
            status, _ = call(
                f"/api/v1/conversations/{cid}/messages",
                {
                    "client_message_id": str(uuid4()),
                    "type": "TEXT",
                    "text": "Local block propagation check",
                },
                alice,
            )
            if status == 403:
                denied = True
                break
            time.sleep(0.25)
        record("block_policy_messaging", denied)
    finally:
        status, _ = call(block_path, token=alice, method="DELETE")
        record("unblock_public_api", status == 200)
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        status, _ = call(
            f"/api/v1/conversations/{cid}/messages",
            {
                "client_message_id": str(uuid4()),
                "type": "TEXT",
                "text": "Local unblock propagation check",
            },
            alice,
        )
        if status in {200, 201}:
            break
        time.sleep(0.25)
    record("unblock_restores_messaging", status in {200, 201})

    status, _ = call("/api/v1/auth/logout", {}, linked["access_token"])
    record("linked_session_logout", status == 200)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - redact sensitive exception details at CLI boundary
        print("Stopped:", type(error).__name__)
        raise SystemExit(1)
