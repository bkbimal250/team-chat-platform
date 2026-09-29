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
from app.registry import RedisMetadataRegistry, Registry
from app.runtime import Runtime

app = FastAPI(title="realtime-service")
# This is always local socket ownership. Production startup attaches shared Redis metadata.
registry = Registry(settings().max_queue_size, instance_id=settings().instance_id)
authorizer = ConversationAuthorizer()
accepting_connections = True
runtime = Runtime()
delivery_task: asyncio.Task | None = None
redis_pubsub = None


def build_production_registry(redis_client: Redis, instance_id: str | None = None) -> Registry:
    """Build one process-local socket registry backed by common Redis metadata."""
    configured = settings()
    owner = instance_id or configured.instance_id
    return Registry(
        configured.max_queue_size,
        metadata_registry=RedisMetadataRegistry(redis_client, owner),
        instance_id=owner,
    )


async def _deliver_remote(payload: dict):
    """Deliver an already-routed event only to this process's local socket."""
    if payload.get("target_instance_id") != settings().instance_id:
        return
    metadata = registry.metadata_registry
    connection = registry.connections.get(payload.get("connection_id", ""))
    try:
        organization_id = UUID(payload["organization_id"])
    except (KeyError, ValueError):
        return
    if not connection or connection.principal.organization_id != organization_id:
        return
    if metadata and not await metadata.claim_delivery(payload.get("delivery_id", "")):
        return
    await registry.enqueue(connection, payload["event"])


async def _listen_for_deliveries(pubsub):
    async for message in pubsub.listen():
        if message.get("type") != "message":
            continue
        try:
            raw = message["data"]
            await _deliver_remote(json.loads(raw.decode() if isinstance(raw, bytes) else raw))
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            continue


@app.on_event("startup")
async def startup():
    """Production requires Redis; development/test may use the local-only registry explicitly."""
    global registry, runtime, delivery_task, redis_pubsub, accepting_connections
    configured = settings()
    accepting_connections = True
    if not configured.redis_url:
        if configured.app_env == "production":
            raise RuntimeError("REDIS_URL is required in production")
        return
    client = Redis.from_url(configured.redis_url)
    try:
        await client.ping()
    except Exception:
        await client.aclose()
        if configured.app_env == "production":
            raise
        return
    registry = build_production_registry(client)
    runtime = Runtime(redis_client=client, metadata_registry=registry.metadata_registry)
    redis_pubsub = client.pubsub()
    await redis_pubsub.subscribe(f"realtime:instance:{configured.instance_id}:deliveries")
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


async def client_event(connection, frame: dict):
    if frame.get("version") != 1:
        raise ProtocolError("PROTOCOL_INVALID", "Unsupported protocol version.")
    event_type = frame.get("type")
    if event_type == "ping":
        return {"version": 1, "type": "pong"}
    if event_type in {"subscribe", "unsubscribe"}:
        conversation_id = UUID(frame["conversation_id"])
        await authorizer.authorize(connection.principal, conversation_id)
        if event_type == "subscribe":
            await registry.subscribe(connection, conversation_id)
        else:
            await registry.unsubscribe(connection, conversation_id)
        return {"version": 1, "type": event_type + ".ok", "conversation_id": str(conversation_id)}
    if event_type in {"typing.start", "typing.stop"}:
        conversation_id = UUID(frame["conversation_id"])
        await authorizer.authorize(connection.principal, conversation_id)
        if conversation_id not in connection.subscriptions:
            raise ProtocolError("CONVERSATION_FORBIDDEN", "Conversation is not subscribed.")
        await registry.set_typing(connection, conversation_id, event_type == "typing.start")
        return {"version": 1, "type": event_type + ".ok"}
    if event_type == "presence.heartbeat":
        await registry.refresh(connection)
        return {"version": 1, "type": event_type + ".ok"}
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
        await registry.remove(connection.id)


@app.on_event("shutdown")
async def shutdown():
    global accepting_connections, delivery_task, redis_pubsub
    accepting_connections = False
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
    await runtime.close()
