import asyncio
import json
import os
from contextlib import suppress
from uuid import UUID

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from redis.asyncio import Redis

from app.auth import authenticate
from app.authorization import ConversationAuthorizer
from app.core import ProtocolError, settings
from app.e2ee_distribution import E2eeDistributionBroadcaster
from app.org_membership import OrgMembershipStore, RedisOrgMembershipStore
from app.presence import PresenceService
from app.registry import RedisMetadataRegistry, Registry
from app.runtime import Runtime
from app.typing import TypingBroadcaster

app = FastAPI(title="realtime-service")
# Avoid loading Settings (and .env production validation) at import time; startup rebinds when configured.
registry = Registry(100, instance_id="local")
membership_store = OrgMembershipStore()
presence_service = PresenceService()
authorizer = ConversationAuthorizer()
accepting_connections = True
runtime = Runtime()
delivery_task: asyncio.Task | None = None
redis_pubsub = None
redis_client: Redis | None = None
typing_broadcaster = TypingBroadcaster(registry, lambda p, cid: authorizer.authorize(p, cid))
e2ee_broadcaster = E2eeDistributionBroadcaster(
    registry, lambda p, cid: authorizer.authorize(p, cid)
)


def build_production_registry(redis_client: Redis, instance_id: str | None = None) -> Registry:
    configured = settings()
    owner = instance_id or configured.instance_id
    store = RedisOrgMembershipStore(redis_client)
    global membership_store, presence_service
    membership_store = store
    presence_service = PresenceService(redis_client, store)
    metadata = RedisMetadataRegistry(redis_client, owner, store)
    return Registry(
        configured.max_queue_size,
        metadata_registry=metadata,
        instance_id=owner,
        membership_store=store,
    )


async def _apply_workspace_revocation(payload: dict):
    try:
        organization_id = UUID(payload["organization_id"])
        member_id = UUID(payload["member_id"])
        status = payload.get("status", "REMOVED")
    except (KeyError, ValueError, TypeError):
        return
    await registry.revoke_workspace_member(organization_id, member_id, status)


async def _deliver_remote(payload: dict):
    if payload.get("target_instance_id") != settings().instance_id:
        return
    if payload.get("type") == "workspace.revoked.v1":
        await _apply_workspace_revocation(payload.get("payload", payload))
        return
    connection = registry.connections.get(payload.get("connection_id", ""))
    try:
        organization_id = (
            UUID(payload["organization_id"]) if payload.get("organization_id") else None
        )
    except (KeyError, ValueError):
        return
    if not connection or connection.principal.organization_id != organization_id:
        return
    if not await registry.workspace_delivery_allowed(connection.principal):
        return
    metadata = registry.metadata_registry
    if metadata and not await metadata.claim_delivery(payload.get("delivery_id", "")):
        return
    frame = payload["event"]
    if frame.get("type") == "typing.updated.v1":
        cid = UUID(frame["payload"]["conversation_id"])
        if cid not in connection.subscriptions:
            return
        try:
            await authorizer.authorize(connection.principal, cid)
        except ProtocolError:
            return
    await registry.enqueue(connection, frame)


async def _listen_for_deliveries(pubsub):
    async for message in pubsub.listen():
        if message.get("type") != "message":
            continue
        try:
            raw = message["data"]
            data = json.loads(raw.decode() if isinstance(raw, bytes) else raw)
            channel = message.get("channel")
            if isinstance(channel, bytes):
                channel = channel.decode()
            if channel == "realtime:workspace-revocations":
                await _apply_workspace_revocation(data)
            else:
                await _deliver_remote(data)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue


@app.on_event("startup")
async def startup():
    global \
        registry, \
        runtime, \
        delivery_task, \
        redis_pubsub, \
        accepting_connections, \
        typing_broadcaster, \
        redis_client, \
        membership_store, \
        presence_service
    configured = settings()
    accepting_connections = True
    if not configured.redis_url:
        if configured.app_env == "production":
            raise RuntimeError("REDIS_URL is required in production")
        registry.membership_store = membership_store
        presence_service = PresenceService(membership_store=membership_store)
        return
    redis_client = Redis.from_url(configured.redis_url)
    try:
        await redis_client.ping()
    except Exception:
        await redis_client.aclose()
        redis_client = None
        if configured.app_env == "production":
            raise
        registry.membership_store = membership_store
        return
    registry = build_production_registry(redis_client)
    presence_service.redis = redis_client

    async def notify_presence(identity_id: UUID, online: bool):
        await registry.broadcast_presence(identity_id, online, presence_service.authorize_watch)

    presence_service._notify_watchers_callback = notify_presence
    typing_broadcaster = TypingBroadcaster(registry, lambda p, cid: authorizer.authorize(p, cid))
    runtime = Runtime(redis_client=redis_client, metadata_registry=registry.metadata_registry)
    redis_pubsub = redis_client.pubsub()
    await redis_pubsub.subscribe(
        f"realtime:instance:{configured.instance_id}:deliveries",
        "realtime:workspace-revocations",
    )
    delivery_task = asyncio.create_task(_listen_for_deliveries(redis_pubsub))


@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}


@app.get("/health/ready", tags=["health"])
async def ready():
    configured = settings()
    redis_url = configured.redis_url or os.getenv("REDIS_URL", "")
    if not redis_url:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    client = Redis.from_url(redis_url)
    try:
        await client.ping()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    finally:
        await client.aclose()
    return {"status": "ready"}


async def sender(websocket: WebSocket, connection):
    while True:
        await websocket.send_json(await connection.queue.get())


async def ensure_workspace_active(principal):
    if principal.organization_id is None:
        return
    store = registry.membership_store or membership_store
    if not await store.is_active(principal.organization_id, principal.member_id):
        raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation access is unavailable.")


async def client_event(connection, frame: dict):
    if frame.get("version") != 1:
        raise ProtocolError("PROTOCOL_INVALID", "Unsupported protocol version.")
    event_type = frame.get("type")
    if event_type == "ping":
        return {"version": 1, "type": "pong"}
    if event_type in {"subscribe", "unsubscribe"}:
        await ensure_workspace_active(connection.principal)
        conversation_id = UUID(frame["conversation_id"])
        await authorizer.authorize(connection.principal, conversation_id)
        if event_type == "subscribe":
            await registry.subscribe(connection, conversation_id)
        else:
            await registry.unsubscribe(connection, conversation_id)
        return {"version": 1, "type": event_type + ".ok", "conversation_id": str(conversation_id)}
    if event_type in {"typing.start", "typing.stop"}:
        await ensure_workspace_active(connection.principal)
        conversation_id = UUID(frame["conversation_id"])
        await authorizer.authorize(connection.principal, conversation_id)
        if conversation_id not in connection.subscriptions:
            raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation is not subscribed.")
        typing_broadcaster.registry = registry
        await typing_broadcaster.update(connection, conversation_id, event_type == "typing.start")
        return {"version": 1, "type": event_type + ".ok"}
    if event_type == "presence.heartbeat":
        await presence_service.touch(connection.principal)
        await registry.refresh(connection)
        return {"version": 1, "type": event_type + ".ok"}
    if event_type == "presence.subscribe":
        await ensure_workspace_active(connection.principal)
        values = frame.get("identity_ids", [])
        if not isinstance(values, list) or len(values) > 50:
            raise ProtocolError("PROTOCOL_INVALID", "Subscribe to at most 50 identities.")
        identity_ids = [UUID(value) for value in values]
        snapshots = []
        for identity_id in identity_ids:
            await presence_service.authorize_watch(connection.principal, identity_id)
            registry.watch_presence(connection, identity_id)
            snapshots.append(await presence_service.snapshot(identity_id))
        return {"version": 1, "type": "presence.snapshot.v1", "identities": snapshots}
    if event_type == "e2ee.sender_key_distribution":
        await ensure_workspace_active(connection.principal)
        conversation_id = UUID(frame["conversation_id"])
        await authorizer.authorize(connection.principal, conversation_id)
        if conversation_id not in connection.subscriptions:
            raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation is not subscribed.")
        e2ee_broadcaster.registry = registry
        await e2ee_broadcaster.publish(
            connection,
            conversation_id,
            {
                "distribution_id": frame["distribution_id"],
                "target_device_id": frame.get("target_device_id"),
                "message_type": frame["message_type"],
                "ciphertext": frame["ciphertext"],
            },
        )
        return {"version": 1, "type": "e2ee.sender_key_distribution.ok"}
    raise ProtocolError("PROTOCOL_INVALID", "Unsupported client event.")


@app.websocket("/api/v1/realtime")
async def realtime(websocket: WebSocket):
    if not accepting_connections or runtime.state != "RUNNING":
        await websocket.close(code=1012)
        return
    token = websocket.query_params.get("token", "")
    try:
        principal = authenticate(token)
    except ProtocolError:
        await websocket.close(code=1008)
        return
    await websocket.accept()
    connection = await registry.register(principal)
    await presence_service.touch(principal)
    await registry.enqueue(
        connection,
        {
            "version": 1,
            "type": "connection.ready.v1",
            "payload": {
                "resubscribe_required": True,
                "backfill": "Use Messaging conversation history for missed messages.",
            },
        },
    )
    sender_task = asyncio.create_task(sender(websocket, connection))
    try:
        while True:
            raw = await websocket.receive_text()
            if len(raw.encode()) > settings().max_frame_bytes:
                raise ProtocolError("FRAME_TOO_LARGE", "Frame is too large.")
            response = await client_event(connection, json.loads(raw))
            await websocket.send_json(response)
    except (WebSocketDisconnect, asyncio.CancelledError):
        pass
    except (ProtocolError, ValueError, json.JSONDecodeError):
        await websocket.close(code=1008)
    finally:
        sender_task.cancel()
        await typing_broadcaster.remove(connection)
        await presence_service.clear(principal)
        await registry.remove(connection.id)


@app.on_event("shutdown")
async def shutdown():
    global accepting_connections, delivery_task, redis_pubsub, redis_client
    accepting_connections = False
    await typing_broadcaster.close()
    for connection in list(registry.connections.values()):
        await registry.remove(connection.id)
    if delivery_task:
        delivery_task.cancel()
        with suppress(asyncio.CancelledError):
            await delivery_task
        delivery_task = None
    if redis_pubsub:
        await redis_pubsub.aclose()
        redis_pubsub = None
    if redis_client:
        await redis_client.aclose()
        redis_client = None
    await runtime.close()
