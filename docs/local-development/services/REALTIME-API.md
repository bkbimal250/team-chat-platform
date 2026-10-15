# Realtime Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | realtime |
| Framework | FastAPI |
| Local Port | 8007 |
| Base URL | http://127.0.0.1:8007 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8007/openapi.json |
| Health URL | http://127.0.0.1:8007/health/ready |
| PostgreSQL database | None owned |
| Redis | Runner endpoint 127.0.0.1:6380/0; actual dependencies in source below |
| RabbitMQ | Runner endpoint 127.0.0.1:5672, vhost `/`; actual workers below |

## Authentication

Health routes are public. Product routes use Identity-issued RS256 tokens and actual service-specific authorization. Internal routes require a service token and are operator-only. Public challenge routes require their documented challenge/OTP/refresh proof. Tenant context is derived from verified tokens; there is no invented X-Organization-ID requirement. Organization permission codes are checked against current tenant role assignments, not merely a frontend role label. See [permission defaults](../../../services/organization-service/common/authorization.py).

## Required Headers

JSON requests: `Content-Type: application/json`. Bearer routes: `Authorization: Bearer {{access_token}}`. Internal routes: `X-Internal-Service-Token: {{internal_service_token}}`. Additional parameters below are from actual schemas. Never attach credentials to signed storage URLs.

## Route Summary

| # | Method | Route | Auth | Role / permission | Purpose |
|---|---|---|---|---|---|
| 1 | GET | `/health/live` | None at this layer | `No fixed application role` | live |
| 2 | GET | `/health/ready` | None at this layer | `No fixed application role` | ready |
| 3 | WEBSOCKET | `/api/v1/realtime` | Access token in query; conversation authorization | `No fixed application role` | realtime |

## GET /health/live

### Purpose

Live

### Authentication

Required: NO. Token: None at this layer. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
(No additional application header required.)
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://127.0.0.1:8007/health/live`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {}
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `REALTIME-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\realtime-service\app\main.py:103](../../../services\realtime-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/live", tags=["health"])
async def live():
    return {"status": "alive"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /health/ready

### Purpose

Ready

### Authentication

Required: NO. Token: None at this layer. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
(No additional application header required.)
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://127.0.0.1:8007/health/ready`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {}
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `REALTIME-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\realtime-service\app\main.py:108](../../../services\realtime-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
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
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## WEBSOCKET /api/v1/realtime

### Purpose

realtime

### Authentication

Required: YES. Token: Access token in query; conversation authorization. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
(No additional application header required.)
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`WEBSOCKET http://127.0.0.1:8007/api/v1/realtime`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `REALTIME-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\realtime-service\app\main.py:157](../../../services\realtime-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
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
        await typing_broadcaster.remove(connection)
        await registry.remove(connection.id)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: `AUTH_INVALID`, `CONVERSATION_FORBIDDEN`, `FRAME_TOO_LARGE`, `PROTOCOL_INVALID`.

Literal event types in implementation/tests: `conversation.closed.v1`, `conversation.member_left.v1`, `conversation.member_removed.v1`, `message.created.v1`, `message.deleted.v1`, `message.delivered.v1`, `message.edited.v1`, `message.reaction_added.v1`, `message.reaction_removed.v1`, `message.read.v1`, `realtime.delivery.v1`, `typing.updated.v1`.

Configuration field names (values omitted): .

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\realtime-service\app\auth.py](../../../services/realtime-service/app/auth.py)
- [services\realtime-service\app\authorization.py](../../../services/realtime-service/app/authorization.py)
- [services\realtime-service\app\consumer_runner.py](../../../services/realtime-service/app/consumer_runner.py)
- [services\realtime-service\tests\contracts\test_message_events.py](../../../services/realtime-service/tests/contracts/test_message_events.py)
- [services\realtime-service\tests\security\test_auth.py](../../../services/realtime-service/tests/security/test_auth.py)
- [services\realtime-service\tests\security\test_tenant_routing.py](../../../services/realtime-service/tests/security/test_tenant_routing.py)
- [services\realtime-service\tests\unit\test_health.py](../../../services/realtime-service/tests/unit/test_health.py)
- [services\realtime-service\tests\unit\test_http_authorization.py](../../../services/realtime-service/tests/unit/test_http_authorization.py)
- [services\realtime-service\tests\unit\test_lifecycle_events.py](../../../services/realtime-service/tests/unit/test_lifecycle_events.py)
- [services\realtime-service\tests\unit\test_protocol.py](../../../services/realtime-service/tests/unit/test_protocol.py)
- [services\realtime-service\tests\unit\test_rabbit_typing.py](../../../services/realtime-service/tests/unit/test_rabbit_typing.py)
- [services\realtime-service\tests\unit\test_redis_metadata.py](../../../services/realtime-service/tests/unit/test_redis_metadata.py)
- [services\realtime-service\tests\unit\test_registry.py](../../../services/realtime-service/tests/unit/test_registry.py)
- [services\realtime-service\tests\unit\test_runtime.py](../../../services/realtime-service/tests/unit/test_runtime.py)
- [services\realtime-service\tests\unit\test_shared_redis_registry.py](../../../services/realtime-service/tests/unit/test_shared_redis_registry.py)
- [services\realtime-service\tests\unit\test_typing_broadcast.py](../../../services/realtime-service/tests/unit/test_typing_broadcast.py)

## WebSocket Frames

[Protocol/manual examples](../testing/WEBSOCKET-TESTING.md). OpenAPI excludes frames; version 1 ping, subscribe/unsubscribe, typing.start/typing.stop and presence.heartbeat are checked by `client_event` in app/main.py.
# Platform administration relevance

No platform realtime metrics or stream route exists in C1. The WebSocket remains participant-authorized; typing and message event payloads are never administration telemetry.

