"""Real local integration checks. Never prints tokens, OTPs, or signed byte URLs."""

import asyncio
import json
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

import websockets

ROOT = Path(__file__).resolve().parents[2]
LOCAL = ROOT / ".local"
BASE = "http://127.0.0.1:8008"
results = {}


def call(path, body=None, token=None, method=None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(
        BASE + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as error:
        return error.code, json.loads(error.read())


def record(name, passed):
    results[name] = "PASS" if passed else "FAIL"
    (LOCAL / "smoke-results.json").write_text(json.dumps(results, indent=2))
    print(name, results[name], flush=True)
    if not passed:
        raise RuntimeError("Local integration failed: " + name)


async def frame(socket, kind):
    async with asyncio.timeout(20):
        while True:
            event = json.loads(await socket.recv())
            if event.get("type") == kind:
                return event


async def main():
    sessions = json.loads((LOCAL / "sessions.json").read_text())
    for index, session in enumerate(sessions):
        status, renewed = call(
            "/api/v1/auth/refresh", {"refresh_token": session["refresh_token"]}
        )
        record(f"refresh_{index}", status == 200)
        session.update(renewed)
    (LOCAL / "sessions.json").write_text(json.dumps(sessions))
    alice, bob = [session["access_token"] for session in sessions]
    status, conversation = call(
        "/api/v1/conversations/direct", {"member_id": sessions[1]["member_id"]}, alice
    )
    record("direct", status in {200, 201})
    cid = conversation["id"]
    (LOCAL / "conversation.json").write_text(json.dumps(conversation))
    uri = "ws://127.0.0.1:8007/api/v1/realtime?token="
    async with (
        websockets.connect(uri + alice) as sender,
        websockets.connect(uri + bob) as recipient,
    ):
        for socket in [sender, recipient]:
            await socket.send(
                json.dumps({"version": 1, "type": "subscribe", "conversation_id": cid})
            )
            await frame(socket, "subscribe.ok")
        record("websocket_authorized_subscriptions", True)
        client_id = str(uuid4())
        body = {
            "client_message_id": client_id,
            "type": "TEXT",
            "text": "Local real integration message",
        }
        status, message = call(f"/api/v1/conversations/{cid}/messages", body, alice)
        record("text_send", status in {200, 201})
        (LOCAL / "message.json").write_text(json.dumps(message))
        received = await frame(recipient, "message.created.v1")
        record(
            "rabbit_to_realtime_message",
            received["payload"].get("conversation_id") == cid,
        )
        status, duplicate = call(f"/api/v1/conversations/{cid}/messages", body, alice)
        record(
            "message_idempotency",
            status in {200, 201} and duplicate.get("id") == message.get("id"),
        )
        for _ in range(20):
            status, rows = call("/api/v1/conversations", token=bob)
            summary = (
                next((row for row in rows if row["id"] == cid), {})
                if isinstance(rows, list)
                else {}
            )
            if summary.get("unread_count", 0) > 0:
                break
            await asyncio.sleep(0.25)
        record(
            "durable_preview_unread",
            status == 200
            and summary.get("unread_count", 0) > 0
            and summary.get("last_message_preview") == body["text"],
        )
        await sender.send(
            json.dumps({"version": 1, "type": "typing.start", "conversation_id": cid})
        )
        typing = await frame(recipient, "typing.updated.v1")
        record("typing", typing["payload"]["conversation_id"] == cid)
        expired_typing = await frame(recipient, "typing.updated.v1")
        record("typing_timeout", expired_typing["payload"]["active"] is False)
        sequence = message["sequence"]
        status, _ = call(
            f"/api/v1/conversations/{cid}/delivered", {"sequence": sequence}, bob
        )
        record("delivery_receipt", status == 200)
        await frame(sender, "message.delivered.v1")
        status, _ = call(
            f"/api/v1/conversations/{cid}/read", {"sequence": sequence}, bob
        )
        record("read_receipt", status == 200)
        await frame(sender, "message.read.v1")
    async with websockets.connect(uri + bob) as socket:
        await socket.send(
            json.dumps({"version": 1, "type": "subscribe", "conversation_id": cid})
        )
        await frame(socket, "subscribe.ok")
        record("reconnect", True)
    status, _history = call(f"/api/v1/conversations/{cid}/messages", token=bob)
    record("message_history", status == 200)
    status, listing = call("/api/v1/conversations", token=bob)
    record("conversation_list", status == 200)
    (LOCAL / "conversation-list.json").write_text(json.dumps(listing))


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as error:  # noqa: BLE001 - redact sensitive exception details at CLI boundary
        # Exception messages may contain a WebSocket URI with a bearer token.
        print("Stopped:", type(error).__name__, flush=True)
        raise SystemExit(1)
