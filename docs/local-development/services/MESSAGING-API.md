# Messaging Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | messaging |
| Framework | FastAPI |
| Local Port | 8004 |
| Base URL | http://127.0.0.1:8004 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8004/openapi.json |
| Health URL | http://127.0.0.1:8004/health/ready |
| PostgreSQL database | teamchat_message_db |
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
| 3 | POST | `/api/v1/conversations/{conversation_id}/messages` | Bearer access token | `Resource membership/ownership checks; see handler` | create |
| 4 | GET | `/api/v1/conversations/{conversation_id}/messages` | Bearer access token | `Resource membership/ownership checks; see handler` | history |
| 5 | PATCH | `/api/v1/messages/{message_id}` | Bearer access token | `Resource membership/ownership checks; see handler` | edit |
| 6 | DELETE | `/api/v1/messages/{message_id}` | Bearer access token | `Resource membership/ownership checks; see handler` | delete |
| 7 | POST | `/api/v1/messages/{message_id}/reactions` | Bearer access token | `Resource membership/ownership checks; see handler` | add reaction |
| 8 | DELETE | `/api/v1/messages/{message_id}/reactions/{reaction}` | Bearer access token | `Resource membership/ownership checks; see handler` | remove reaction |
| 9 | POST | `/api/v1/conversations/{conversation_id}/delivered` | Bearer access token | `Resource membership/ownership checks; see handler` | delivered |
| 10 | POST | `/api/v1/conversations/{conversation_id}/read` | Bearer access token | `Resource membership/ownership checks; see handler` | read |

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

`GET http://127.0.0.1:8004/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:18](../../../services\messaging-service\app\main.py). Dependencies: See middleware/handler.

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

`GET http://127.0.0.1:8004/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:23](../../../services\messaging-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready", tags=["health"])
async def ready():
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        from fastapi.responses import JSONResponse

        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {"status": "ready"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{conversation_id}/messages

### Purpose

Create

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
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `client_message_id` | YES | `{"type": "string", "format": "uuid"}` |
| `type` | NO | `{"type": "string", "default": "TEXT"}` |
| `text` | NO | `{"anyOf": [{"type": "string", "maxLength": 10000, "minLength": 1}, {"type": "null"}]}` |
| `media_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |
| `reply_to_message_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "client_message_id": {
      "type": "string",
      "format": "uuid",
      "title": "Client Message Id"
    },
    "type": {
      "type": "string",
      "title": "Type",
      "default": "TEXT"
    },
    "text": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 10000,
          "minLength": 1
        },
        {
          "type": "null"
        }
      ],
      "title": "Text"
    },
    "media_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Media Id"
    },
    "reply_to_message_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Reply To Message Id"
    }
  },
  "type": "object",
  "required": [
    "client_message_id"
  ],
  "title": "SendMessage"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/{conversation_id}/messages`

```json
{
  "client_message_id": "{{replace_with_actual_uuid}}",
  "type": "TEXT",
  "text": "{{replace_with_valid_value}}",
  "media_id": "{{replace_with_actual_uuid}}",
  "reply_to_message_id": "{{replace_with_actual_uuid}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:44](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/conversations/{conversation_id}/messages")
async def create(
    conversation_id: UUID,
    body: SendMessage,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await send(db, p, conversation_id, body, request.headers.get("X-Correlation-ID", ""))
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/conversations/{conversation_id}/messages

### Purpose

History

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
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    }
  },
  {
    "name": "before_sequence",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Before Sequence"
    }
  },
  {
    "name": "after_sequence",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "After Sequence"
    }
  },
  {
    "name": "limit",
    "in": "query",
    "required": false,
    "schema": {
      "type": "integer",
      "default": 50,
      "title": "Limit"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/conversations/{conversation_id}/messages`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:56](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/conversations/{conversation_id}/messages")
async def history(
    conversation_id: UUID,
    before_sequence: int | None = None,
    after_sequence: int | None = None,
    limit: int = 50,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    await authorize(db, p, conversation_id)
    q = (
        select(Message)
        .where(
            Message.organization_id == p.organization_id, Message.conversation_id == conversation_id
        )
        .order_by(Message.sequence)
        .limit(min(limit, 100))
    )
    if before_sequence:
        q = q.where(Message.sequence < before_sequence)
    if after_sequence:
        q = q.where(Message.sequence > after_sequence)
    return list((await db.scalars(q)).all())
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/messages/{message_id}

### Purpose

Edit

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
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `text` | YES | `{"type": "string", "maxLength": 10000, "minLength": 1}` |

```json
{
  "properties": {
    "text": {
      "type": "string",
      "maxLength": 10000,
      "minLength": 1,
      "title": "Text"
    }
  },
  "type": "object",
  "required": [
    "text"
  ],
  "title": "EditMessage"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/messages/{message_id}`

```json
{
  "text": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:81](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.patch("/api/v1/messages/{message_id}")
async def edit(
    message_id: UUID,
    body: EditMessage,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        m = await db.scalar(
            select(Message)
            .where(Message.id == message_id, Message.organization_id == p.organization_id)
            .with_for_update()
        )
        if not m or m.sender_member_id != p.member_id or m.type != "TEXT" or m.deleted_at:
            raise DomainError("MESSAGE_EDIT_FORBIDDEN", "Message cannot be edited.", 403)
        m.text = body.text
        m.edited_at = datetime.now(UTC)
        db.add(event(m, "message.edited.v1", request.headers.get("X-Correlation-ID", "")))
        return m
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/messages/{message_id}

### Purpose

Delete

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
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`DELETE http://localhost:8008/api/v1/messages/{message_id}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:103](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/messages/{message_id}")
async def delete(
    message_id: UUID,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        m = await db.scalar(
            select(Message)
            .where(Message.id == message_id, Message.organization_id == p.organization_id)
            .with_for_update()
        )
        if not m or m.sender_member_id != p.member_id:
            raise DomainError("MESSAGE_DELETE_FORBIDDEN", "Message cannot be deleted.", 403)
        m.deleted_at = datetime.now(UTC)
        m.status = "DELETED"
        m.text = None
        db.add(event(m, "message.deleted.v1", request.headers.get("X-Correlation-ID", "")))
        return {"status": "DELETED"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/messages/{message_id}/reactions

### Purpose

Add Reaction

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
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `reaction` | YES | `{"type": "string", "maxLength": 64, "minLength": 1}` |

```json
{
  "properties": {
    "reaction": {
      "type": "string",
      "maxLength": 64,
      "minLength": 1,
      "title": "Reaction"
    }
  },
  "type": "object",
  "required": [
    "reaction"
  ],
  "title": "ReactionInput"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/messages/{message_id}/reactions`

```json
{
  "reaction": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:125](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/messages/{message_id}/reactions")
async def add_reaction(
    message_id: UUID,
    body: ReactionInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        message = await db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.organization_id == p.organization_id,
                Message.deleted_at.is_(None),
            )
        )
        if not message:
            raise DomainError("MESSAGE_NOT_FOUND", "Message is unavailable.", 404)
        await authorize(db, p, message.conversation_id)
        row = await db.scalar(
            select(MessageReaction).where(
                MessageReaction.message_id == message_id,
                MessageReaction.member_id == p.member_id,
                MessageReaction.reaction == body.reaction,
            )
        )
        if row:
            return row
        row = MessageReaction(
            message_id=message_id,
            organization_id=p.organization_id,
            user_id=p.user_id,
            member_id=p.member_id,
            reaction=body.reaction,
        )
        db.add(row)
        db.add(
            event(message, "message.reaction_added.v1", request.headers.get("X-Correlation-ID", ""))
        )
        return row
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/messages/{message_id}/reactions/{reaction}

### Purpose

Remove Reaction

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
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
    }
  },
  {
    "name": "reaction",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Reaction"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`DELETE http://localhost:8008/api/v1/messages/{message_id}/reactions/{reaction}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:167](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/messages/{message_id}/reactions/{reaction}")
async def remove_reaction(
    message_id: UUID,
    reaction: str,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        message = await db.scalar(
            select(Message).where(
                Message.id == message_id,
                Message.organization_id == p.organization_id,
                Message.deleted_at.is_(None),
            )
        )
        if not message:
            raise DomainError("MESSAGE_NOT_FOUND", "Message is unavailable.", 404)
        await authorize(db, p, message.conversation_id)
        row = await db.scalar(
            select(MessageReaction).where(
                MessageReaction.message_id == message_id,
                MessageReaction.member_id == p.member_id,
                MessageReaction.reaction == reaction,
            )
        )
        if row:
            await db.delete(row)
            db.add(
                event(
                    message,
                    "message.reaction_removed.v1",
                    request.headers.get("X-Correlation-ID", ""),
                )
            )
        return {"status": "REMOVED"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{conversation_id}/delivered

### Purpose

Delivered

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
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `sequence` | YES | `{"type": "integer", "minimum": 1.0}` |

```json
{
  "properties": {
    "sequence": {
      "type": "integer",
      "minimum": 1.0,
      "title": "Sequence"
    }
  },
  "type": "object",
  "required": [
    "sequence"
  ],
  "title": "SequenceInput"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/{conversation_id}/delivered`

```json
{
  "sequence": 1.0
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:205](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/conversations/{conversation_id}/delivered")
async def delivered(
    conversation_id: UUID,
    body: SequenceInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await mark(
            db,
            p,
            conversation_id,
            body.sequence,
            False,
            request.headers.get("X-Correlation-ID", ""),
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{conversation_id}/read

### Purpose

Read

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
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    }
  },
  {
    "name": "authorization",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Authorization"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `sequence` | YES | `{"type": "integer", "minimum": 1.0}` |

```json
{
  "properties": {
    "sequence": {
      "type": "integer",
      "minimum": 1.0,
      "title": "Sequence"
    }
  },
  "type": "object",
  "required": [
    "sequence"
  ],
  "title": "SequenceInput"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/{conversation_id}/read`

```json
{
  "sequence": 1.0
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MESSAGING-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\messaging-service\app\main.py:224](../../../services\messaging-service\app\main.py). Dependencies: app.security.principal, app.db.get_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/conversations/{conversation_id}/read")
async def read(
    conversation_id: UUID,
    body: SequenceInput,
    request: Request,
    p: Principal = Depends(principal),
    db: AsyncSession = Depends(get_session),
):
    async with db.begin():
        return await mark(
            db, p, conversation_id, body.sequence, True, request.headers.get("X-Correlation-ID", "")
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: `ACCESS_TOKEN_INVALID`, `CONVERSATION_FORBIDDEN`, `DIRECT_CONVERSATION_BLOCKED`, `MEDIA_NOT_READY`, `MEDIA_TYPE_MISMATCH`, `MEDIA_UNAVAILABLE`, `MESSAGE_DELETE_FORBIDDEN`, `MESSAGE_EDIT_FORBIDDEN`, `MESSAGE_NOT_FOUND`, `MESSAGE_TYPE_UNSUPPORTED`, `READ_INVALID`, `REPLY_INVALID`.

Literal event types in implementation/tests: `conversation.closed.v1`, `conversation.created.v1`, `conversation.member_added.v1`, `conversation.member_left.v1`, `conversation.member_removed.v1`, `conversation.member_role_changed.v1`, `conversation.ownership_transferred.v1`, `conversation.summary.message.v1`, `conversation.summary.read.v1`, `conversation.updated.v1`, `media.deleted.v1`, `media.failed.v1`, `media.ready.v1`, `message.created.v1`, `message.deleted.v1`, `message.delivered.v1`, `message.edited.v1`, `message.reaction_added.v1`, `message.reaction_removed.v1`, `message.read.v1`, `user.blocked.v1`, `user.unblocked.v1`.

Configuration field names (values omitted): .

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\messaging-service\alembic\versions\0001_initial.py](../../../services/messaging-service/alembic/versions/0001_initial.py)
- [services\messaging-service\alembic\versions\0002_media_messages.py](../../../services/messaging-service/alembic/versions/0002_media_messages.py)
- [services\messaging-service\app\consumer_runner.py](../../../services/messaging-service/app/consumer_runner.py)
- [services\messaging-service\app\models.py](../../../services/messaging-service/app/models.py)
- [services\messaging-service\app\outbox_runner.py](../../../services/messaging-service/app/outbox_runner.py)
- [services\messaging-service\app\schemas.py](../../../services/messaging-service/app/schemas.py)
- [services\messaging-service\app\security.py](../../../services/messaging-service/app/security.py)
- [services\messaging-service\tests\contracts\test_events.py](../../../services/messaging-service/tests/contracts/test_events.py)
- [services\messaging-service\tests\contracts\test_phase5_contracts.py](../../../services/messaging-service/tests/contracts/test_phase5_contracts.py)
- [services\messaging-service\tests\security\test_media_messages.py](../../../services/messaging-service/tests/security/test_media_messages.py)
- [services\messaging-service\tests\security\test_phase5_boundaries.py](../../../services/messaging-service/tests/security/test_phase5_boundaries.py)
- [services\messaging-service\tests\security\test_tenant.py](../../../services/messaging-service/tests/security/test_tenant.py)
- [services\messaging-service\tests\unit\test_block_policy.py](../../../services/messaging-service/tests/unit/test_block_policy.py)
- [services\messaging-service\tests\unit\test_global_block_event.py](../../../services/messaging-service/tests/unit/test_global_block_event.py)
- [services\messaging-service\tests\unit\test_health.py](../../../services/messaging-service/tests/unit/test_health.py)
- [services\messaging-service\tests\unit\test_history_reactions.py](../../../services/messaging-service/tests/unit/test_history_reactions.py)
- [services\messaging-service\tests\unit\test_media_persistence.py](../../../services/messaging-service/tests/unit/test_media_persistence.py)
- [services\messaging-service\tests\unit\test_message_routes.py](../../../services/messaging-service/tests/unit/test_message_routes.py)
- [services\messaging-service\tests\unit\test_message_services.py](../../../services/messaging-service/tests/unit/test_message_services.py)
- [services\messaging-service\tests\unit\test_messaging.py](../../../services/messaging-service/tests/unit/test_messaging.py)
- [services\messaging-service\tests\unit\test_production_config.py](../../../services/messaging-service/tests/unit/test_production_config.py)
- [services\messaging-service\tests\unit\test_summary_backfill.py](../../../services/messaging-service/tests/unit/test_summary_backfill.py)
- [services\messaging-service\tests\unit\test_transport.py](../../../services/messaging-service/tests/unit/test_transport.py)
# Platform administration relevance

No platform message diagnostic route exists in C1. Message bodies and reaction/receipt data stay participant-authorized and are excluded from generic administrative access.

