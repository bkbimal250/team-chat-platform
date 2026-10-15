# Notification Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | notification |
| Framework | FastAPI |
| Local Port | 8006 |
| Base URL | http://127.0.0.1:8006 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8006/openapi.json |
| Health URL | http://127.0.0.1:8006/health/ready |
| PostgreSQL database | teamchat_notification_db |
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
| 3 | PUT | `/api/v1/notifications/devices/current/token` | Bearer access token | `Resource membership/ownership checks; see handler` | put token |
| 4 | DELETE | `/api/v1/notifications/devices/current/token` | Bearer access token | `Resource membership/ownership checks; see handler` | delete token |
| 5 | GET | `/api/v1/notifications/preferences` | Bearer access token | `Resource membership/ownership checks; see handler` | get preferences |
| 6 | PATCH | `/api/v1/notifications/preferences` | Bearer access token | `Resource membership/ownership checks; see handler` | patch preferences |
| 7 | GET | `/api/v1/notifications` | Bearer access token | `Resource membership/ownership checks; see handler` | list notifications |

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

`GET http://127.0.0.1:8006/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:26](../../../services\notification-service\app\main.py). Dependencies: See middleware/handler.

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

`GET http://127.0.0.1:8006/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:31](../../../services\notification-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready", tags=["health"])
async def ready():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PUT /api/v1/notifications/devices/current/token

### Purpose

Put Token

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "authorization",
    "in": "header",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `platform` | YES | `{"type": "string"}` |
| `provider` | YES | `{"type": "string"}` |
| `push_token` | YES | `{"type": "string"}` |

```json
{
  "properties": {
    "platform": {
      "type": "string",
      "title": "Platform"
    },
    "provider": {
      "type": "string",
      "title": "Provider"
    },
    "push_token": {
      "type": "string",
      "title": "Push Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "platform",
    "provider",
    "push_token"
  ],
  "title": "TokenRequest"
}
```

### Postman Request

`PUT http://localhost:8008/api/v1/notifications/devices/current/token`

```json
{
  "platform": "{{replace_with_valid_value}}",
  "provider": "{{replace_with_valid_value}}",
  "push_token": "{{replace_with_valid_value}}"
}
```

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
  },
  "422": {
    "description": "Validation Error",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/HTTPValidationError"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:41](../../../services\notification-service\app\main.py). Dependencies: app.security.get_principal, app.db.get_db_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.put("/api/v1/notifications/devices/current/token")
async def put_token(
    request: TokenRequest,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        return await PushTokenRepository(session).upsert_current_device(principal, request)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/notifications/devices/current/token

### Purpose

Delete Token

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "authorization",
    "in": "header",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`DELETE http://localhost:8008/api/v1/notifications/devices/current/token`

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
  },
  "422": {
    "description": "Validation Error",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/HTTPValidationError"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:51](../../../services\notification-service\app\main.py). Dependencies: app.security.get_principal, app.db.get_db_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/notifications/devices/current/token")
async def delete_token(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        await PushTokenRepository(session).disable_current_device(principal)
    return {"status": "disabled"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/notifications/preferences

### Purpose

Get Preferences

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "authorization",
    "in": "header",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/notifications/preferences`

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
  },
  "422": {
    "description": "Validation Error",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/HTTPValidationError"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:60](../../../services\notification-service\app\main.py). Dependencies: app.security.get_principal, app.db.get_db_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/notifications/preferences")
async def get_preferences(
    principal: Principal = Depends(get_principal), session: AsyncSession = Depends(get_db_session)
):
    async with session.begin():
        return await PreferenceRepository(session).get_or_create(principal)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/notifications/preferences

### Purpose

Patch Preferences

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "authorization",
    "in": "header",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `push_enabled` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `message_notifications` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `group_notifications` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `notification_preview` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `sound_enabled` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `vibration_enabled` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "push_enabled": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Push Enabled"
    },
    "message_notifications": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Message Notifications"
    },
    "group_notifications": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Group Notifications"
    },
    "notification_preview": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Notification Preview"
    },
    "sound_enabled": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Sound Enabled"
    },
    "vibration_enabled": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Vibration Enabled"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "title": "PreferencePatch"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/notifications/preferences`

```json
{
  "push_enabled": false,
  "message_notifications": false,
  "group_notifications": false,
  "notification_preview": "{{replace_with_valid_value}}",
  "sound_enabled": false,
  "vibration_enabled": false
}
```

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
  },
  "422": {
    "description": "Validation Error",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/HTTPValidationError"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:68](../../../services\notification-service\app\main.py). Dependencies: app.security.get_principal, app.db.get_db_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.patch("/api/v1/notifications/preferences")
async def patch_preferences(
    request: PreferencePatch,
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    async with session.begin():
        row = await PreferenceRepository(session).get_or_create(principal)
        if request.push_enabled is not None:
            row.push_enabled = request.push_enabled
        if request.notification_preview is not None:
            row.preview = request.notification_preview
        return row
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/notifications

### Purpose

List Notifications

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "limit",
    "in": "query",
    "required": false,
    "schema": {
      "type": "integer",
      "maximum": 100,
      "minimum": 1,
      "default": 20,
      "title": "Limit"
    }
  },
  {
    "name": "offset",
    "in": "query",
    "required": false,
    "schema": {
      "type": "integer",
      "minimum": 0,
      "default": 0,
      "title": "Offset"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/notifications`

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
  },
  "422": {
    "description": "Validation Error",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/HTTPValidationError"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `NOTIFICATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\notification-service\app\main.py:83](../../../services\notification-service\app\main.py). Dependencies: app.security.get_principal, app.db.get_db_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/notifications")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    principal: Principal = Depends(get_principal),
    session: AsyncSession = Depends(get_db_session),
):
    from app.models import Notification

    rows = (
        await session.scalars(
            select(Notification)
            .where(
                Notification.organization_id == principal.organization_id,
                Notification.recipient_member_id == principal.member_id,
                Notification.recipient_user_id == principal.user_id,
            )
            .order_by(Notification.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    return [
        {
            "id": str(row.id),
            "conversation_id": str(row.conversation_id),
            "message_id": str(row.message_id),
            "title": row.title,
            "body": row.body,
            "preview_mode": row.preview_mode,
        }
        for row in rows
    ]
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: .

Literal event types in implementation/tests: `conversation.closed.v1`, `conversation.created.v1`, `conversation.member_added.v1`, `conversation.member_left.v1`, `conversation.member_removed.v1`, `conversation.member_role_changed.v1`, `conversation.ownership_transferred.v1`, `conversation.state_updated.v1`, `conversation.updated.v1`, `device.revoked.v1`, `member.activated.v2`, `member.created.v2`, `member.left.v2`, `member.removed.v2`, `member.role_changed.v2`, `member.suspended.v2`, `member.updated.v2`, `message.created.v1`, `notification.created.v1`, `notification.failed.v1`, `notification.sent.v1`, `push_token.invalidated.v1`, `user.blocked.v1`, `user.created.v1`, `user.preferences_updated.v1`, `user.privacy_updated.v1`, `user.profile_updated.v1`, `user.unblocked.v1`.

Configuration field names (values omitted): `app_env`, `database_url`, `delivery_poll_seconds`, `firebase_credentials_json`, `jwt_algorithm`, `jwt_audience`, `jwt_issuer`, `jwt_public_key`, `push_provider`, `rabbitmq_url`.

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\notification-service\alembic\versions\0001_initial.py](../../../services/notification-service/alembic/versions/0001_initial.py)
- [services\notification-service\alembic\versions\0002_notification_pipeline.py](../../../services/notification-service/alembic/versions/0002_notification_pipeline.py)
- [services\notification-service\alembic\versions\0003_global_user_projection.py](../../../services/notification-service/alembic/versions/0003_global_user_projection.py)
- [services\notification-service\alembic\versions\0004_notification_preferences.py](../../../services/notification-service/alembic/versions/0004_notification_preferences.py)
- [services\notification-service\alembic\versions\0005_delivery_recovery_fields.py](../../../services/notification-service/alembic/versions/0005_delivery_recovery_fields.py)
- [services\notification-service\app\config.py](../../../services/notification-service/app/config.py)
- [services\notification-service\app\consumer_runner.py](../../../services/notification-service/app/consumer_runner.py)
- [services\notification-service\app\delivery_worker.py](../../../services/notification-service/app/delivery_worker.py)
- [services\notification-service\app\message_notification_consumer.py](../../../services/notification-service/app/message_notification_consumer.py)
- [services\notification-service\app\models.py](../../../services/notification-service/app/models.py)
- [services\notification-service\app\outbox_runner.py](../../../services/notification-service/app/outbox_runner.py)
- [services\notification-service\app\projection_consumers.py](../../../services/notification-service/app/projection_consumers.py)
- [services\notification-service\app\schemas.py](../../../services/notification-service/app/schemas.py)
- [services\notification-service\app\security.py](../../../services/notification-service/app/security.py)
- [services\notification-service\tests\contracts\test_contracts.py](../../../services/notification-service/tests/contracts/test_contracts.py)
- [services\notification-service\tests\security\test_final_readiness_security.py](../../../services/notification-service/tests/security/test_final_readiness_security.py)
- [services\notification-service\tests\security\test_inbox.py](../../../services/notification-service/tests/security/test_inbox.py)
- [services\notification-service\tests\security\test_production_readiness.py](../../../services/notification-service/tests/security/test_production_readiness.py)
- [services\notification-service\tests\security\test_security.py](../../../services/notification-service/tests/security/test_security.py)
- [services\notification-service\tests\unit\test_delivery_recovery_schema.py](../../../services/notification-service/tests/unit/test_delivery_recovery_schema.py)
- [services\notification-service\tests\unit\test_delivery_worker.py](../../../services/notification-service/tests/unit/test_delivery_worker.py)
- [services\notification-service\tests\unit\test_message_notification_consumer.py](../../../services/notification-service/tests/unit/test_message_notification_consumer.py)
- [services\notification-service\tests\unit\test_notifications.py](../../../services/notification-service/tests/unit/test_notifications.py)
- [services\notification-service\tests\unit\test_pipeline_models.py](../../../services/notification-service/tests/unit/test_pipeline_models.py)
- [services\notification-service\tests\unit\test_preference_repository.py](../../../services/notification-service/tests/unit/test_preference_repository.py)
- [services\notification-service\tests\unit\test_projection_consumers.py](../../../services/notification-service/tests/unit/test_projection_consumers.py)
- [services\notification-service\tests\unit\test_rabbit_outbox.py](../../../services/notification-service/tests/unit/test_rabbit_outbox.py)
- [services\notification-service\tests\unit\test_repositories.py](../../../services/notification-service/tests/unit/test_repositories.py)
# Platform administration relevance

No platform notification diagnostic route exists in C1. Recipient notifications, provider state and device tokens remain private; provider credentials are never returned.

