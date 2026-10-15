# Conversation Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | conversation |
| Framework | FastAPI |
| Local Port | 8003 |
| Base URL | http://127.0.0.1:8003 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8003/api/schema/ |
| Health URL | http://127.0.0.1:8003/health/ready |
| PostgreSQL database | conversation_db |
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
| 3 | POST | `/api/v1/conversations/direct` | Bearer access token | `Resource membership/ownership checks; see handler` | direct |
| 4 | POST | `/api/v1/conversations/groups` | Bearer access token | `Resource membership/ownership checks; see handler` | group |
| 5 | GET | `/api/v1/conversations` | Bearer access token | `Resource membership/ownership checks; see handler` | list conversations |
| 6 | GET | `/api/v1/conversations/{cid}` | Bearer access token | `Resource membership/ownership checks; see handler` | get |
| 7 | POST | `/api/v1/conversations/{cid}/members` | Bearer access token | `Resource membership/ownership checks; see handler` | add |
| 8 | DELETE | `/api/v1/conversations/{cid}/members/{mid}` | Bearer access token | `Resource membership/ownership checks; see handler` | remove |
| 9 | POST | `/api/v1/conversations/{cid}/leave` | Bearer access token | `Resource membership/ownership checks; see handler` | leave |
| 10 | POST | `/api/v1/conversations/{cid}/close` | Bearer access token | `Resource membership/ownership checks; see handler` | close |
| 11 | GET | `/api/v1/conversations/{cid}/members` | Bearer access token | `Resource membership/ownership checks; see handler` | members |
| 12 | POST | `/api/v1/conversations/{cid}/members/{mid}/promote` | Bearer access token | `Resource membership/ownership checks; see handler` | promote |
| 13 | POST | `/api/v1/conversations/{cid}/members/{mid}/demote` | Bearer access token | `Resource membership/ownership checks; see handler` | demote |
| 14 | POST | `/api/v1/conversations/{cid}/transfer-ownership` | Bearer access token | `Resource membership/ownership checks; see handler` | transfer |
| 15 | PATCH | `/api/v1/conversations/{cid}` | Bearer access token | `Resource membership/ownership checks; see handler` | update |
| 16 | PATCH | `/api/v1/conversations/{cid}/state` | Bearer access token | `Resource membership/ownership checks; see handler` | state |
| 17 | POST | `/internal/v1/conversations/{cid}/authorize` | Internal service token | `Service caller only` | authorize send |

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

`GET http://127.0.0.1:8003/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\main.py:48](../../../services\conversation-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/live")
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

`GET http://127.0.0.1:8003/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\main.py:53](../../../services\conversation-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready")
async def ready(request: Request):
    try:
        async with Sessions() as s:
            await s.execute(text("SELECT 1"))
        await request.app.state.redis.ping()
    except Exception:
        return JSONResponse({"status": "not_ready"}, status_code=503)
    return {
        "status": "ready",
        "database": "available",
        "redis": "available",
        "broker": "asynchronous",
    }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/direct

### Purpose

Direct

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
| `member_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "properties": {
    "member_id": {
      "type": "string",
      "format": "uuid",
      "title": "Member Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "member_id"
  ],
  "title": "DirectIn"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/direct`

```json
{
  "member_id": "{{replace_with_actual_uuid}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:88](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/direct", status_code=201)
async def direct(
    payload: DirectIn, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c, created = await ConversationService().direct(
            session, *p, payload.member_id, request.state.correlation_id
        )
    return out(c) | {"created": created}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/groups

### Purpose

Group

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
| `title` | YES | `{"type": "string", "maxLength": 200, "minLength": 1}` |
| `description` | NO | `{"anyOf": [{"type": "string", "maxLength": 2000}, {"type": "null"}]}` |
| `member_ids` | YES | `{"type": "array", "maxItems": 10000, "minItems": 1}` |

```json
{
  "properties": {
    "title": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Title"
    },
    "description": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 2000
        },
        {
          "type": "null"
        }
      ],
      "title": "Description"
    },
    "member_ids": {
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "type": "array",
      "maxItems": 10000,
      "minItems": 1,
      "title": "Member Ids"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "title",
    "member_ids"
  ],
  "title": "GroupIn"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/groups`

```json
{
  "title": "{{replace_with_valid_value}}",
  "description": "{{replace_with_valid_value}}",
  "member_ids": [
    "{{replace_with_actual_uuid}}"
  ]
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:99](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/groups", status_code=201)
async def group(
    payload: GroupIn, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await ConversationService().group(session, *p, payload, request.state.correlation_id)
    return out(c)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/conversations

### Purpose

List Conversations

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
    "name": "type",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "$ref": "#/components/schemas/CType"
        },
        {
          "type": "null"
        }
      ],
      "title": "Type"
    }
  },
  {
    "name": "archived",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Archived"
    }
  },
  {
    "name": "pinned",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Pinned"
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

`GET http://localhost:8008/api/v1/conversations`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:108](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("")
async def list_conversations(
    type: CType | None = None,
    archived: bool | None = None,
    pinned: bool | None = None,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    org, mid = p
    counts = (
        select(ConversationMember.conversation_id, func.count(ConversationMember.id).label("count"))
        .where(
            ConversationMember.organization_id == org, ConversationMember.status == MStatus.ACTIVE
        )
        .group_by(ConversationMember.conversation_id)
        .subquery()
    )
    q = (
        select(Conversation, ConversationMember, MemberState, counts.c.count)
        .join(ConversationMember, ConversationMember.conversation_id == Conversation.id)
        .join(counts, counts.c.conversation_id == Conversation.id)
        .join(
            MemberState,
            (MemberState.conversation_id == Conversation.id) & (MemberState.member_id == mid),
        )
        .where(
            ConversationMember.member_id == mid,
            ConversationMember.status == MStatus.ACTIVE,
            Conversation.organization_id == org,
        )
        .group_by(Conversation.id, ConversationMember.id, MemberState.id, counts.c.count)
    )
    if type:
        q = q.where(Conversation.type == type)
    if archived is not None:
        q = q.where(MemberState.is_archived == archived)
    if pinned is not None:
        q = q.where(MemberState.is_pinned == pinned)
    rows = (await session.execute(q)).all()
    summary = await summaries(session, org, mid, [c.id for c, _, _, _ in rows])
    return [out(c, m, s, count) | summary[c.id] for c, m, s, count in rows]
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/conversations/{cid}

### Purpose

Get

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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

`GET http://localhost:8008/api/v1/conversations/{cid}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:151](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("/{cid}")
async def get(cid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    c = await get_conversation(cid, p[0], session)
    m = await ConversationService().mine(session, c.id, p[1])
    Authorization.view(m)
    s = (
        await session.execute(
            select(MemberState).where(
                MemberState.conversation_id == c.id, MemberState.member_id == p[1]
            )
        )
    ).scalar_one()
    return out(c, m, s)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/members

### Purpose

Add

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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
| `member_ids` | YES | `{"type": "array", "maxItems": 10000, "minItems": 1}` |

```json
{
  "properties": {
    "member_ids": {
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "type": "array",
      "maxItems": 10000,
      "minItems": 1,
      "title": "Member Ids"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "member_ids"
  ],
  "title": "MemberIds"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/{cid}/members`

```json
{
  "member_ids": [
    "{{replace_with_actual_uuid}}"
  ]
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:166](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/members")
async def add(
    cid: UUID,
    payload: MemberIds,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        members = await ConversationService().add(
            session, c, p[1], payload.member_ids, request.state.correlation_id
        )
    return {"added_member_ids": members}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/conversations/{cid}/members/{mid}

### Purpose

Remove

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
    }
  },
  {
    "name": "mid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Mid"
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

`DELETE http://localhost:8008/api/v1/conversations/{cid}/members/{mid}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:182](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.delete("/{cid}/members/{mid}")
async def remove(
    cid: UUID,
    mid: UUID,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().remove(session, c, p[1], mid, request.state.correlation_id)
    return {"status": "REMOVED"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/leave

### Purpose

Leave

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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

`POST http://localhost:8008/api/v1/conversations/{cid}/leave`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:196](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/leave")
async def leave(
    cid: UUID, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().remove(
            session, c, p[1], p[1], request.state.correlation_id, True
        )
    return {"status": "LEFT"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/close

### Purpose

Close

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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

`POST http://localhost:8008/api/v1/conversations/{cid}/close`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:208](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/close")
async def close(
    cid: UUID, request: Request, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.manage(await ConversationService().mine(session, c.id, p[1]))
        if c.status != CStatus.CLOSED:
            c.status, c.closed_at = CStatus.CLOSED, datetime.now(UTC)
            await event(
                session, "conversation.closed.v1", c, request.state.correlation_id, ["status"]
            )
    return out(c)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/conversations/{cid}/members

### Purpose

Members

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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

`GET http://localhost:8008/api/v1/conversations/{cid}/members`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:223](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("/{cid}/members")
async def members(cid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    c = await get_conversation(cid, p[0], session)
    Authorization.view(await ConversationService().mine(session, c.id, p[1]))
    rows = (
        (
            await session.execute(
                select(ConversationMember)
                .where(ConversationMember.conversation_id == c.id)
                .order_by(ConversationMember.joined_at)
            )
        )
        .scalars()
        .all()
    )
    return [
        {
            "member_id": str(x.member_id),
            "user_id": str(x.user_id) if x.user_id else None,
            "role": x.role,
            "status": x.status,
        }
        for x in rows
    ]
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/members/{mid}/promote

### Purpose

Promote

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
    }
  },
  {
    "name": "mid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Mid"
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

`POST http://localhost:8008/api/v1/conversations/{cid}/members/{mid}/promote`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:249](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/members/{mid}/promote")
async def promote(cid: UUID, mid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.owner(await ConversationService().mine(session, c.id, p[1]))
        m = await ConversationService().mine(session, c.id, mid)
        Authorization.view(m)
        if m.role == MRole.OWNER:
            raise DomainError("OWNER_ROLE_IMMUTABLE", "Ownership requires transfer.", 409)
        old_role = m.role
        m.role = MRole.ADMIN
        await event(session, "conversation.member_role_changed.v1", c, "", ["members"], m, old_role)
    return {"status": "ADMIN"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/members/{mid}/demote

### Purpose

Demote

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
    }
  },
  {
    "name": "mid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Mid"
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

`POST http://localhost:8008/api/v1/conversations/{cid}/members/{mid}/demote`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:264](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/members/{mid}/demote")
async def demote(cid: UUID, mid: UUID, p=Depends(principal), session: AsyncSession = Depends(db)):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.owner(await ConversationService().mine(session, c.id, p[1]))
        m = await ConversationService().mine(session, c.id, mid)
        Authorization.view(m)
        if m.role == MRole.OWNER:
            raise DomainError("OWNER_ROLE_IMMUTABLE", "Ownership requires transfer.", 409)
        old_role = m.role
        m.role = MRole.MEMBER
        await event(session, "conversation.member_role_changed.v1", c, "", ["members"], m, old_role)
    return {"status": "MEMBER"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/conversations/{cid}/transfer-ownership

### Purpose

Transfer

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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
| `member_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "properties": {
    "member_id": {
      "type": "string",
      "format": "uuid",
      "title": "Member Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "member_id"
  ],
  "title": "Transfer"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/conversations/{cid}/transfer-ownership`

```json
{
  "member_id": "{{replace_with_actual_uuid}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:279](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{cid}/transfer-ownership")
async def transfer(
    cid: UUID,
    payload: Transfer,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        await ConversationService().transfer(
            session, c, p[1], payload.member_id, request.state.correlation_id
        )
    return {"status": "TRANSFERRED"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/conversations/{cid}

### Purpose

Update

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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
| `title` | NO | `{"anyOf": [{"type": "string", "maxLength": 200}, {"type": "null"}]}` |
| `description` | NO | `{"anyOf": [{"type": "string", "maxLength": 2000}, {"type": "null"}]}` |
| `avatar_media_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "title": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 200
        },
        {
          "type": "null"
        }
      ],
      "title": "Title"
    },
    "description": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 2000
        },
        {
          "type": "null"
        }
      ],
      "title": "Description"
    },
    "avatar_media_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Avatar Media Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "title": "UpdateConversation"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/conversations/{cid}`

```json
{
  "title": "{{replace_with_valid_value}}",
  "description": "{{replace_with_valid_value}}",
  "avatar_media_id": "{{replace_with_actual_uuid}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:295](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.patch("/{cid}")
async def update(
    cid: UUID,
    payload: UpdateConversation,
    request: Request,
    p=Depends(principal),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        if c.type != CType.GROUP:
            raise DomainError("GROUP_REQUIRED", "Only groups can be updated.", 422)
        Authorization.manage(await ConversationService().mine(session, c.id, p[1]))
        for k, v in payload.model_dump(exclude_unset=True).items():
            if k == "title" and (v is None or not v.strip()):
                raise DomainError("GROUP_TITLE_INVALID", "A group title is required.", 422)
            setattr(c, k, v.strip() if k == "title" and v else v)
        await event(
            session, "conversation.updated.v1", c, request.state.correlation_id, ["metadata"]
        )
    return out(c)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/conversations/{cid}/state

### Purpose

State

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
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
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
| `is_archived` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `is_pinned` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `muted_until` | NO | `{"anyOf": [{"type": "string", "format": "date-time"}, {"type": "null"}]}` |
| `is_muted_forever` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `notification_level` | NO | `{"anyOf": [{"type": "string", "pattern": "^(ALL|MENTIONS|NONE)$"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "is_archived": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Is Archived"
    },
    "is_pinned": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Is Pinned"
    },
    "muted_until": {
      "anyOf": [
        {
          "type": "string",
          "format": "date-time"
        },
        {
          "type": "null"
        }
      ],
      "title": "Muted Until"
    },
    "is_muted_forever": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Is Muted Forever"
    },
    "notification_level": {
      "anyOf": [
        {
          "type": "string",
          "pattern": "^(ALL|MENTIONS|NONE)$"
        },
        {
          "type": "null"
        }
      ],
      "title": "Notification Level"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "title": "StateIn"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/conversations/{cid}/state`

```json
{
  "is_archived": false,
  "is_pinned": false,
  "muted_until": "{{replace_with_valid_timestamp}}",
  "is_muted_forever": false,
  "notification_level": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:318](../../../services\conversation-service\app\api.py). Dependencies: app.api.principal, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.patch("/{cid}/state")
async def state(
    cid: UUID, payload: StateIn, p=Depends(principal), session: AsyncSession = Depends(db)
):
    async with session.begin():
        c = await get_conversation(cid, p[0], session)
        Authorization.view(await ConversationService().mine(session, c.id, p[1]))
        s = (
            await session.execute(
                select(MemberState)
                .where(MemberState.conversation_id == c.id, MemberState.member_id == p[1])
                .with_for_update()
            )
        ).scalar_one()
        for k, v in payload.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        member = await ConversationService().mine(session, c.id, p[1])
        await event(session, "conversation.state_updated.v1", c, "", ["state"], member, state=s)
    return {"status": "UPDATED"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /internal/v1/conversations/{cid}/authorize

### Purpose

Authorize Send

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "cid",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Cid"
    }
  },
  {
    "name": "x-internal-service-token",
    "in": "header",
    "required": true,
    "schema": {
      "type": "string",
      "title": "X-Internal-Service-Token"
    }
  }
]
```

### Request Body

No declared object properties; see schema and response implementation.

```json
{
  "type": "object",
  "additionalProperties": true,
  "title": "Body"
}
```

### Postman Request

`POST http://127.0.0.1:8003/internal/v1/conversations/{cid}/authorize`

```json
{}
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `CONVERSATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\conversation-service\app\api.py:339](../../../services\conversation-service\app\api.py). Dependencies: app.api.internal_service, app.db.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@internal_router.post("/{cid}/authorize")
async def authorize_send(
    cid: UUID,
    body: dict,
    _: None = Depends(internal_service),
    session: AsyncSession = Depends(db),
):
    organization_id, member_id = UUID(body["organization_id"]), UUID(body["member_id"])
    c = await get_conversation(cid, organization_id, session)
    member = await ConversationService().mine(session, c.id, member_id)
    allowed = c.status == "ACTIVE" and member is not None and member.status == MStatus.ACTIVE
    if allowed and c.type == CType.DIRECT:
        peers = (
            await session.scalars(
                select(ConversationMember).where(
                    ConversationMember.conversation_id == c.id,
                    ConversationMember.member_id != member_id,
                )
            )
        ).all()
        for peer in peers:
            blocked = await session.scalar(
                select(BlockProjection.id).where(
                    (
                        (BlockProjection.blocker_user_id == member.user_id)
                        & (BlockProjection.blocked_user_id == peer.user_id)
                    )
                    | (
                        (BlockProjection.blocker_user_id == peer.user_id)
                        & (BlockProjection.blocked_user_id == member.user_id)
                    )
                )
            )
            allowed = allowed and not bool(blocked)
    return {
        "allowed": allowed,
        "conversation_id": str(c.id),
        "organization_id": str(c.organization_id),
        "conversation_type": c.type,
        "member_id": str(member_id),
        "user_id": str(member.user_id) if member and member.user_id else None,
        "member_status": member.status if member else None,
    }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: `CONVERSATION_NOT_FOUND`, `CONVERSATION_OWNER_REQUIRED`, `CONVERSATION_PERMISSION_DENIED`, `DIRECT_CONVERSATION_BLOCKED`, `DIRECT_SELF_NOT_ALLOWED`, `GROUP_MEMBER_LIMIT`, `GROUP_REQUIRED`, `GROUP_TITLE_INVALID`, `MEMBER_IDENTITY_UNAVAILABLE`, `NOT_AUTHENTICATED`, `OWNERSHIP_TRANSFER_REQUIRED`, `OWNER_ROLE_IMMUTABLE`.

Literal event types in implementation/tests: `conversation.closed.v1`, `conversation.created.v1`, `conversation.member_added.v1`, `conversation.member_left.v1`, `conversation.member_removed.v1`, `conversation.member_role_changed.v1`, `conversation.ownership_transferred.v1`, `conversation.state_updated.v1`, `conversation.summary.message.v1`, `conversation.summary.read.v1`, `conversation.updated.v1`, `message.created.v1`, `message.deleted.v1`, `message.edited.v1`, `message.read.v1`, `user.blocked.v1`, `user.unblocked.v1`.

Configuration field names (values omitted): .

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\conversation-service\alembic\versions\0001_initial.py](../../../services/conversation-service/alembic/versions/0001_initial.py)
- [services\conversation-service\alembic\versions\0002_chat_summaries.py](../../../services/conversation-service/alembic/versions/0002_chat_summaries.py)
- [services\conversation-service\app\api.py](../../../services/conversation-service/app/api.py)
- [services\conversation-service\app\consumer_runner.py](../../../services/conversation-service/app/consumer_runner.py)
- [services\conversation-service\app\models.py](../../../services/conversation-service/app/models.py)
- [services\conversation-service\app\outbox.py](../../../services/conversation-service/app/outbox.py)
- [services\conversation-service\app\outbox_runner.py](../../../services/conversation-service/app/outbox_runner.py)
- [services\conversation-service\app\schemas.py](../../../services/conversation-service/app/schemas.py)
- [services\conversation-service\tests\contracts\test_conversation_event_contracts.py](../../../services/conversation-service/tests/contracts/test_conversation_event_contracts.py)
- [services\conversation-service\tests\security\test_conversation_security.py](../../../services/conversation-service/tests/security/test_conversation_security.py)
- [services\conversation-service\tests\security\test_direct_chat_blocks.py](../../../services/conversation-service/tests/security/test_direct_chat_blocks.py)
- [services\conversation-service\tests\unit\test_chat_projection.py](../../../services/conversation-service/tests/unit/test_chat_projection.py)
- [services\conversation-service\tests\unit\test_close_contract_fields.py](../../../services/conversation-service/tests/unit/test_close_contract_fields.py)
- [services\conversation-service\tests\unit\test_conversation_behavior.py](../../../services/conversation-service/tests/unit/test_conversation_behavior.py)
- [services\conversation-service\tests\unit\test_member_rejoin.py](../../../services/conversation-service/tests/unit/test_member_rejoin.py)
# Platform administration relevance

No platform conversation diagnostic route exists in C1. Conversation routes require participant authorization; private member and lifecycle data is not exposed to generic administrators.



## Personal direct conversations (Phase 3)
`POST /api/v1/conversations/personal/direct` accepts only `{"contact_id":"<owned saved contact UUID>"}` with a personal access token (no org/mid). User Service revalidates owned contact, current discoverability, active target and mutual blocks. Arbitrary user IDs are rejected. Response includes `id`, `scope: PERSONAL`, and `created`. Reverse and concurrent requests resolve to one durable pair.

Existing list/detail/messages/state/media/realtime routes are reused. Personal actor IDs in legacy `member_id` fields mean authenticated Identity IDs; workspace actor IDs remain organization membership IDs. A null organization is never sufficient authorization: the conversation's active participant must match. Personal rows never appear in workspace queries. Current block checks fail closed through the internal Conversation -> User authorization path.

Migrations: Conversation/Messaging/Media each add `0003_personal_direct`, after their existing 0002 head. Downgrade refuses to discard personal rows: archive/migrate data explicitly before attempting to restore non-null workspace columns. No production migration was run.
