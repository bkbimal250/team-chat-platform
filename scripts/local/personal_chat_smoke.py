"""Exercise personal chat through the loopback Gateway without external providers."""

import asyncio
import hashlib
import json
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from uuid import uuid4

import websockets

from scripts.local import dev

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local"
BASE = "http://127.0.0.1:8008"


def call(path, body=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method or ("POST" if body is not None else "GET"),
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        try:
            return error.code, json.loads(error.read())
        except (ValueError, json.JSONDecodeError):
            return error.code, {}


def record(name, passed, detail=None):
    result = "PASS" if passed else "FAIL"
    if not passed and detail:
        result += " (" + detail + ")"
    print(name, result, flush=True)
    if not passed:
        raise RuntimeError(name)


def personal_account(label):
    for _ in range(10):
        suffix = uuid4().hex
        phone = "+120255501" + str(secrets.randbelow(100)).zfill(2)
        payload = {
            "display_name": "Local " + label,
            "email": label.lower() + "-" + suffix + "@example.test",
            "phone": phone,
            "password": secrets.token_urlsafe(24),
            "device": {
                "installation_id": suffix,
                "platform": "WEB",
                "device_name": "Personal chat smoke",
            },
        }
        status, tokens = call("/api/v1/auth/registration/personal", payload)
        if status == 201:
            record(
                label.lower() + "_zero_org_registration",
                tokens.get("organization_id") is None and tokens.get("member_id") is None,
            )
            return tokens["access_token"], phone
        if status != 409:
            break
    record(label.lower() + "_registration", False)
    raise RuntimeError("personal_registration_failed")


def eligible_contact(token, phone):
    status, contact = call(
        "/api/v1/contacts",
        {"phone": phone, "country": "US", "local_label": "Personal chat smoke"},
        token,
    )
    record("save_personal_contact", status in {200, 201})
    contact_id = contact["id"]
    for _ in range(30):
        status, contact = call("/api/v1/contacts/" + contact_id, token=token)
        if status == 200 and contact.get("matched_user"):
            return contact
        time.sleep(0.25)
    raise RuntimeError("contact_match_unavailable")


async def receive(socket, event_type):
    async with asyncio.timeout(20):
        while True:
            frame = json.loads(await socket.recv())
            if frame.get("type") == event_type:
                return frame


async def verify_realtime(conversation_id, alice_token, bob_token, outsider_token):
    uri = "ws://127.0.0.1:8007/api/v1/realtime?token="
    async with (
        websockets.connect(uri + alice_token) as sender,
        websockets.connect(uri + bob_token) as recipient,
    ):
        for socket in (sender, recipient):
            await socket.send(
                json.dumps(
                    {"version": 1, "type": "subscribe", "conversation_id": conversation_id}
                )
            )
            await receive(socket, "subscribe.ok")
        record("personal_realtime_subscribe", True)

        await sender.send(
            json.dumps(
                {"version": 1, "type": "typing.start", "conversation_id": conversation_id}
            )
        )
        typing = await receive(recipient, "typing.updated.v1")
        record("personal_typing", typing["payload"]["active"] is True)

        status, message = call(
            f"/api/v1/conversations/{conversation_id}/messages",
            {
                "client_message_id": str(uuid4()),
                "type": "TEXT",
                "text": "Personal realtime delivery",
            },
            alice_token,
        )
        record("personal_realtime_send", status in {200, 201})
        delivered = await receive(recipient, "message.created.v1")
        record(
            "personal_realtime_message",
            delivered["payload"]["conversation_id"] == conversation_id,
        )

        status, _ = call(
            f"/api/v1/conversations/{conversation_id}/delivered",
            {"sequence": message["sequence"]},
            bob_token,
        )
        record("personal_delivery_receipt", status == 200)
        await receive(sender, "message.delivered.v1")
        status, _ = call(
            f"/api/v1/conversations/{conversation_id}/read",
            {"sequence": message["sequence"]},
            bob_token,
        )
        record("personal_read_receipt", status == 200)
        await receive(sender, "message.read.v1")

    async with websockets.connect(uri + bob_token) as reconnected:
        await reconnected.send(
            json.dumps(
                {"version": 1, "type": "subscribe", "conversation_id": conversation_id}
            )
        )
        await receive(reconnected, "subscribe.ok")
        record("personal_reconnect", True)

    try:
        async with websockets.connect(uri + outsider_token) as outsider:
            await outsider.send(
                json.dumps(
                    {"version": 1, "type": "subscribe", "conversation_id": conversation_id}
                )
            )
            await receive(outsider, "subscribe.ok")
    except websockets.exceptions.ConnectionClosed as error:
        record("personal_realtime_nonparticipant_denied", error.code == 1008)
    else:
        record("personal_realtime_nonparticipant_denied", False)


def verify_media(token, recipient_token, conversation_id, outsider_token):
    fixtures = [
        ("image.png", "image/png", "image", "IMAGE"),
        ("video.mp4", "video/mp4", "video", "VIDEO"),
        ("audio.wav", "audio/wav", "audio", "AUDIO"),
        ("voice.webm", "audio/webm", "audio", "VOICE"),
        ("document.pdf", "application/pdf", "document", "DOCUMENT"),
    ]
    for filename, mime_type, category, message_type in fixtures:
        data = (LOCAL / "fixtures" / filename).read_bytes()
        status, upload = call(
            "/api/v1/media/uploads",
            {
                "conversation_id": conversation_id,
                "filename": filename,
                "mime_type": mime_type,
                "size_bytes": len(data),
                "media_type": category,
                "checksum_sha256": hashlib.sha256(data).hexdigest(),
            },
            token,
        )
        record("personal_media_upload_" + category, status == 201)
        request = urllib.request.Request(
            upload["upload_url"],
            data=data,
            method="PUT",
            headers=upload["required_headers"],
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            record("personal_media_bytes_" + category, response.status == 200)
        media_id = upload["media_id"]
        status, _ = call(f"/api/v1/media/{media_id}/complete", {}, token)
        record("personal_media_complete_" + category, status == 200)

        message_body = {
            "client_message_id": str(uuid4()),
            "type": message_type,
            "media_id": media_id,
        }
        for _ in range(20):
            status, _ = call(
                f"/api/v1/conversations/{conversation_id}/messages", message_body, token
            )
            if status in {200, 201}:
                break
            time.sleep(0.25)
        record("personal_media_message_" + category, status in {200, 201})
        status, download = call(f"/api/v1/media/{media_id}/download", token=recipient_token)
        record("personal_media_recipient_" + category, status == 200)
        with urllib.request.urlopen(download["download_url"], timeout=15) as response:
            record("personal_media_download_" + category, response.read() == data)

    status, _ = call(
        "/api/v1/media/uploads",
        {
            "conversation_id": conversation_id,
            "filename": "outsider.png",
            "mime_type": "image/png",
            "size_bytes": 1,
            "media_type": "image",
        },
        outsider_token,
    )
    record("personal_media_nonparticipant_denied", status == 403)


def main():
    local = dev.env("identity")
    if local.get("APP_ENV") != "development" or local.get("OTP_PROVIDER") != "development":
        raise RuntimeError("local_development_runner_required")

    alice_token, alice_phone = personal_account("Alice")
    bob_token, bob_phone = personal_account("Bob")
    outsider_token, _ = personal_account("Charlie")
    alice_contact = eligible_contact(alice_token, bob_phone)
    bob_contact = eligible_contact(bob_token, alice_phone)
    alice_user = call("/api/v1/users/me", token=alice_token)[1]
    bob_user = call("/api/v1/users/me", token=bob_token)[1]

    status, alice_conversation = call(
        "/api/v1/conversations/personal/direct",
        {"contact_id": alice_contact["id"]},
        alice_token,
    )
    record("personal_direct_create", status in {200, 201})
    conversation_id = alice_conversation["id"]
    status, reverse = call(
        "/api/v1/conversations/personal/direct",
        {"contact_id": bob_contact["id"]},
        bob_token,
    )
    record("personal_reverse_unique", status in {200, 201} and reverse["id"] == conversation_id)
    status, _ = call(
        "/api/v1/conversations/personal/direct",
        {"contact_id": str(uuid4())},
        alice_token,
    )
    record("arbitrary_contact_denied", status == 404)
    status, _ = call(
        "/api/v1/conversations/direct",
        {"member_id": bob_user["user_id"]},
        alice_token,
    )
    record("personal_user_id_creation_denied", status in {401, 403})
    status, _ = call(
        f"/api/v1/conversations/{conversation_id}", token=outsider_token
    )
    record("personal_conversation_nonparticipant_denied", status == 404)
    status, _ = call(
        f"/api/v1/conversations/{conversation_id}/messages", token=outsider_token
    )
    record("personal_history_nonparticipant_denied", status == 403)

    status, message = call(
        f"/api/v1/conversations/{conversation_id}/messages",
        {
            "client_message_id": str(uuid4()),
            "type": "TEXT",
            "text": "Personal message history",
        },
        alice_token,
    )
    record(
        "personal_message_send",
        status in {200, 201},
        f"HTTP {status} {message.get('error', {}).get('code', '')}",
    )
    status, history = call(
        f"/api/v1/conversations/{conversation_id}/messages", token=bob_token
    )
    record(
        "personal_message_history",
        status == 200 and any(row["id"] == message["id"] for row in history),
    )
    status, edited = call(
        f"/api/v1/messages/{message['id']}",
        {"text": "Edited personal message"},
        alice_token,
        "PATCH",
    )
    record("personal_message_edit", status == 200 and edited["text"] == "Edited personal message")
    status, reaction = call(
        f"/api/v1/messages/{message['id']}/reactions",
        {"reaction": "👍"},
        bob_token,
    )
    record("personal_message_reaction", status == 200)
    status, _ = call(
        "/api/v1/messages/"
        + message["id"]
        + "/reactions/"
        + urllib.parse.quote("👍", safe=""),
        token=bob_token,
        method="DELETE",
    )
    record("personal_message_unreaction", status == 200)
    status, _ = call(
        f"/api/v1/messages/{message['id']}", token=alice_token, method="DELETE"
    )
    record("personal_message_delete", status == 200)

    status, _ = call(
        "/api/v1/users/me/privacy", {"discoverable": False}, bob_token, "PATCH"
    )
    record("personal_privacy_update", status == 200)
    try:
        status, unavailable = call(
            "/api/v1/contacts/" + alice_contact["id"], token=alice_token
        )
        record(
            "personal_discoverability_hides_contact",
            status == 200 and unavailable.get("matched_user") is None,
        )
        status, _ = call(
            "/api/v1/conversations/personal/direct",
            {"contact_id": alice_contact["id"]},
            alice_token,
        )
        record("personal_privacy_denies_new_direct", status == 404)
    finally:
        status, _ = call(
            "/api/v1/users/me/privacy", {"discoverable": True}, bob_token, "PATCH"
        )
        record("personal_privacy_restore", status == 200)

    asyncio.run(
        verify_realtime(conversation_id, alice_token, bob_token, outsider_token)
    )
    verify_media(alice_token, bob_token, conversation_id, outsider_token)

    status, _ = call(f"/api/v1/users/{bob_user['user_id']}/block", {}, alice_token)
    record("personal_block", status == 200)
    try:
        denied = False
        for _ in range(20):
            status, _ = call(
                f"/api/v1/conversations/{conversation_id}/messages",
                {
                    "client_message_id": str(uuid4()),
                    "type": "TEXT",
                    "text": "Blocked personal message",
                },
                alice_token,
            )
            if status == 403:
                denied = True
                break
            time.sleep(0.25)
        record("personal_block_denies_messages", denied)
        media_data = (LOCAL / "fixtures" / "image.png").read_bytes()
        status, _ = call(
            "/api/v1/media/uploads",
            {
                "conversation_id": conversation_id,
                "filename": "blocked.png",
                "mime_type": "image/png",
                "size_bytes": len(media_data),
                "media_type": "image",
                "checksum_sha256": hashlib.sha256(media_data).hexdigest(),
            },
            alice_token,
        )
        record("personal_block_denies_media", status == 403)
    finally:
        status, _ = call(
            f"/api/v1/users/{bob_user['user_id']}/block",
            token=alice_token,
            method="DELETE",
        )
        record("personal_unblock", status == 200)


if __name__ == "__main__":
    try:
        main()
    except Exception as error:  # noqa: BLE001 - avoid logging auth data or signed media URLs
        print("Stopped:", type(error).__name__, flush=True)
        raise SystemExit(1)
