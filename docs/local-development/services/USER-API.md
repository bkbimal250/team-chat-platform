# User Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | user |
| Framework | FastAPI |
| Local Port | 8002 |
| Base URL | http://127.0.0.1:8002 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8002/openapi.json |
| Health URL | http://127.0.0.1:8002/health/ready |
| PostgreSQL database | teamchat_user_db |
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
| 3 | POST | `/internal/v1/users/block-check` | Internal service token | `Service caller only` | block check |
| 4 | POST | `/internal/v1/users/projections` | Internal service token | `Service caller only` | projections |
| 5 | GET | `/api/v1/users/me` | Bearer access token | `Resource membership/ownership checks; see handler` | me |
| 6 | PATCH | `/api/v1/users/me` | Bearer access token | `Resource membership/ownership checks; see handler` | update me |
| 7 | GET | `/api/v1/users/me/preferences` | Bearer access token | `Resource membership/ownership checks; see handler` | preferences |
| 8 | PATCH | `/api/v1/users/me/preferences` | Bearer access token | `Resource membership/ownership checks; see handler` | update preferences |
| 9 | POST | `/api/v1/users/{user_id}/block` | Bearer access token | `Resource membership/ownership checks; see handler` | block |
| 10 | DELETE | `/api/v1/users/{user_id}/block` | Bearer access token | `Resource membership/ownership checks; see handler` | unblock |
| 11 | GET | `/api/v1/users/me/privacy` | Bearer access token | `Resource membership/ownership checks; see handler` | privacy |
| 12 | PATCH | `/api/v1/users/me/privacy` | Bearer access token | `Resource membership/ownership checks; see handler` | update privacy |
| 13 | GET | `/api/v1/users/me/blocked` | Bearer access token | `Resource membership/ownership checks; see handler` | blocked users |
| 14 | GET | `/api/v1/users/search` | Bearer access token | `Resource membership/ownership checks; see handler` | search users |
| 15 | GET | `/api/v1/users/{user_id}` | Bearer access token | `Resource membership/ownership checks; see handler` | get profile |
| 16 | POST | `/internal/v1/users/company-owner` | Internal service token | `Service caller only` | provision owner |
| 17 | POST | `/internal/v1/users/provision` | Internal service token | `Service caller only` | provision owner |

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

`GET http://127.0.0.1:8002/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:210](../../../services\user-service\app\main.py). Dependencies: See middleware/handler.

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

`GET http://127.0.0.1:8002/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:215](../../../services\user-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready")
async def ready():
    try:
        async with sessions() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        raise HTTPException(503, "service not ready") from None
    return {"status": "ready"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /internal/v1/users/block-check

### Purpose

Block Check

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

| Field | Required | Type / constraints |
|---|---|---|
| `user_a_id` | YES | `{"type": "string", "format": "uuid"}` |
| `user_b_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "properties": {
    "user_a_id": {
      "type": "string",
      "format": "uuid",
      "title": "User A Id"
    },
    "user_b_id": {
      "type": "string",
      "format": "uuid",
      "title": "User B Id"
    }
  },
  "type": "object",
  "required": [
    "user_a_id",
    "user_b_id"
  ],
  "title": "BlockCheck"
}
```

### Postman Request

`POST http://127.0.0.1:8002/internal/v1/users/block-check`

```json
{
  "user_a_id": "{{replace_with_actual_uuid}}",
  "user_b_id": "{{replace_with_actual_uuid}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:225](../../../services\user-service\app\main.py). Dependencies: app.main.internal, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/internal/v1/users/block-check", dependencies=[Depends(internal)])
async def block_check(body: BlockCheck, session: AsyncSession = Depends(db)):
    # Internal callers may hold an Identity ID from Organization membership events.
    a_ids = select(User.id).where(
        (User.id == body.user_a_id) | (User.identity_id == body.user_a_id)
    )
    b_ids = select(User.id).where(
        (User.id == body.user_b_id) | (User.identity_id == body.user_b_id)
    )
    q = select(UserBlock.id).where(
        ((UserBlock.blocker_user_id.in_(a_ids)) & (UserBlock.blocked_user_id.in_(b_ids)))
        | ((UserBlock.blocker_user_id.in_(b_ids)) & (UserBlock.blocked_user_id.in_(a_ids)))
    )
    return {"blocked": await session.scalar(q) is not None}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /internal/v1/users/projections

### Purpose

Projections

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

| Field | Required | Type / constraints |
|---|---|---|
| `user_ids` | YES | `{"type": "array", "maxItems": 100}` |

```json
{
  "properties": {
    "user_ids": {
      "items": {
        "type": "string",
        "format": "uuid"
      },
      "type": "array",
      "maxItems": 100,
      "title": "User Ids"
    }
  },
  "type": "object",
  "required": [
    "user_ids"
  ],
  "title": "ProjectionRequest"
}
```

### Postman Request

`POST http://127.0.0.1:8002/internal/v1/users/projections`

```json
{
  "user_ids": [
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:241](../../../services\user-service\app\main.py). Dependencies: app.main.internal, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/internal/v1/users/projections", dependencies=[Depends(internal)])
async def projections(body: ProjectionRequest, session: AsyncSession = Depends(db)):
    users = (await session.scalars(select(User).where(User.id.in_(body.user_ids)))).all()
    return {
        "users": [
            {
                "user_id": str(u.id),
                "display_name": u.display_name,
                "avatar_media_id": str(u.avatar_media_id) if u.avatar_media_id else None,
                "status": u.status,
            }
            for u in users
        ]
    }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/me

### Purpose

Me

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/me`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:257](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/me")
async def me(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    return projection(await current_user(session, context))
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/users/me

### Purpose

Update Me

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `display_name` | NO | `{"anyOf": [{"type": "string", "maxLength": 200}, {"type": "null"}]}` |
| `avatar_media_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |
| `about` | NO | `{"anyOf": [{"type": "string", "maxLength": 2000}, {"type": "null"}]}` |

```json
{
  "properties": {
    "display_name": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 200
        },
        {
          "type": "null"
        }
      ],
      "title": "Display Name"
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
    },
    "about": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 2000
        },
        {
          "type": "null"
        }
      ],
      "title": "About"
    }
  },
  "type": "object",
  "title": "ProfilePatch"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/users/me`

```json
{
  "display_name": "{{replace_with_valid_value}}",
  "avatar_media_id": "{{replace_with_actual_uuid}}",
  "about": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:265](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.patch("/api/v1/users/me")
async def update_me(
    body: ProfilePatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(user, key, value)
        outbox(session, user, "user.profile_updated.v1")
    return projection(user)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/me/preferences

### Purpose

Preferences

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/me/preferences`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:279](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/me/preferences")
async def preferences(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    value = await session.get(UserPreferences, user.id)
    if not value:
        raise HTTPException(404, "preferences not provisioned")
    return {key: getattr(value, key) for key in SettingsPatch.model_fields}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/users/me/preferences

### Purpose

Update Preferences

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `language` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `timezone` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `theme_preference` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `enter_to_send` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `media_auto_download` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |
| `link_preview_enabled` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "language": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Language"
    },
    "timezone": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Timezone"
    },
    "theme_preference": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Theme Preference"
    },
    "enter_to_send": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Enter To Send"
    },
    "media_auto_download": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Media Auto Download"
    },
    "link_preview_enabled": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Link Preview Enabled"
    }
  },
  "type": "object",
  "title": "SettingsPatch"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/users/me/preferences`

```json
{
  "language": "{{replace_with_valid_value}}",
  "timezone": "{{replace_with_valid_value}}",
  "theme_preference": "{{replace_with_valid_value}}",
  "enter_to_send": false,
  "media_auto_download": false,
  "link_preview_enabled": false
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:291](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.patch("/api/v1/users/me/preferences")
async def update_preferences(
    body: SettingsPatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        value = await session.get(UserPreferences, user.id)
        if not value:
            value = UserPreferences(user_id=user.id)
            session.add(value)
        for key, item in body.model_dump(exclude_unset=True).items():
            setattr(value, key, item)
        outbox(session, user, "user.preferences_updated.v1")
    return {key: getattr(value, key) for key in SettingsPatch.model_fields}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/users/{user_id}/block

### Purpose

Block

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
    "name": "user_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "User Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/users/{user_id}/block`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:309](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/users/{user_id}/block")
async def block(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        if user.id == user_id:
            raise HTTPException(422, "cannot block yourself")
        target = await session.get(User, user_id)
        if target is None:
            raise HTTPException(404, "user not found")
        item = await session.scalar(
            select(UserBlock).where(
                UserBlock.blocker_user_id == user.id, UserBlock.blocked_user_id == user_id
            )
        )
        if not item:
            session.add(UserBlock(blocker_user_id=user.id, blocked_user_id=user_id))
            outbox(
                session,
                user,
                "user.blocked.v1",
                {
                    "blocker_user_id": str(user.id),
                    "blocked_user_id": str(target.id),
                    "blocker_identity_id": str(user.identity_id),
                    "blocked_identity_id": str(target.identity_id),
                },
            )
    return {"blocked": True}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/users/{user_id}/block

### Purpose

Unblock

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
    "name": "user_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "User Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`DELETE http://localhost:8008/api/v1/users/{user_id}/block`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:343](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/users/{user_id}/block")
async def unblock(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    async with session.begin():
        user = await current_user(session, context)
        target = await session.get(User, user_id)
        if target is None:
            raise HTTPException(404, "user not found")
        item = await session.scalar(
            select(UserBlock).where(
                UserBlock.blocker_user_id == user.id, UserBlock.blocked_user_id == user_id
            )
        )
        if item:
            await session.delete(item)
            outbox(
                session,
                user,
                "user.unblocked.v1",
                {
                    "blocker_user_id": str(user.id),
                    "blocked_user_id": str(target.id),
                    "blocker_identity_id": str(user.identity_id),
                    "blocked_identity_id": str(target.identity_id),
                },
            )
    return {"blocked": False}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/me/privacy

### Purpose

Privacy

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/me/privacy`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:375](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/me/privacy")
async def privacy(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    value = await session.get(UserPrivacySettings, user.id)
    if value is None:
        raise HTTPException(404, "privacy settings not provisioned")
    return {key: getattr(value, key) for key in PrivacyPatch.model_fields}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/users/me/privacy

### Purpose

Update Privacy

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `profile_photo_visibility` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `about_visibility` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `online_status_visibility` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `last_seen_visibility` | NO | `{"anyOf": [{"type": "string"}, {"type": "null"}]}` |
| `read_receipts_enabled` | NO | `{"anyOf": [{"type": "boolean"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "profile_photo_visibility": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Profile Photo Visibility"
    },
    "about_visibility": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "About Visibility"
    },
    "online_status_visibility": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Online Status Visibility"
    },
    "last_seen_visibility": {
      "anyOf": [
        {
          "type": "string"
        },
        {
          "type": "null"
        }
      ],
      "title": "Last Seen Visibility"
    },
    "read_receipts_enabled": {
      "anyOf": [
        {
          "type": "boolean"
        },
        {
          "type": "null"
        }
      ],
      "title": "Read Receipts Enabled"
    }
  },
  "type": "object",
  "title": "PrivacyPatch"
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/users/me/privacy`

```json
{
  "profile_photo_visibility": "{{replace_with_valid_value}}",
  "about_visibility": "{{replace_with_valid_value}}",
  "online_status_visibility": "{{replace_with_valid_value}}",
  "last_seen_visibility": "{{replace_with_valid_value}}",
  "read_receipts_enabled": false
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:387](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.patch("/api/v1/users/me/privacy")
async def update_privacy(
    body: PrivacyPatch,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    allowed = {"EVERYONE", "ORGANIZATION", "CONTACTS", "NOBODY"}
    async with session.begin():
        user = await current_user(session, context)
        value = await session.get(UserPrivacySettings, user.id)
        if value is None:
            value = UserPrivacySettings(user_id=user.id)
            session.add(value)
        for key, item in body.model_dump(exclude_unset=True).items():
            if key.endswith("visibility") and item not in allowed:
                raise HTTPException(422, "invalid visibility")
            setattr(value, key, item)
        outbox(session, user, "user.privacy_updated.v1")
    return {key: getattr(value, key) for key in PrivacyPatch.model_fields}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/me/blocked

### Purpose

Blocked Users

### Authentication

Required: YES. Token: Bearer access token. Role/permission: Resource membership/ownership checks; see handler. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/me/blocked`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:408](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/me/blocked")
async def blocked_users(
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    user = await current_user(session, context)
    rows = await session.scalars(
        select(User)
        .join(UserBlock, UserBlock.blocked_user_id == User.id)
        .where(UserBlock.blocker_user_id == user.id)
    )
    return {"users": [projection(item) for item in rows]}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/search

### Purpose

Search Users

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
    "name": "q",
    "in": "query",
    "required": false,
    "schema": {
      "type": "string",
      "default": "",
      "title": "Q"
    }
  },
  {
    "name": "limit",
    "in": "query",
    "required": false,
    "schema": {
      "type": "integer",
      "default": 20,
      "title": "Limit"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/search`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:422](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/search")
async def search_users(
    q: str = "",
    limit: int = 20,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    if len(q.strip()) < 2:
        raise HTTPException(422, "query must contain at least two characters")
    limit = min(max(limit, 1), 50)
    query = (
        select(User, MembershipProjection.member_id)
        .join(MembershipProjection, MembershipProjection.user_id == User.id)
        .where(
            MembershipProjection.organization_id == context.organization_id,
            MembershipProjection.status == "ACTIVE",
            User.status == "ACTIVE",
            User.display_name.ilike(f"%{q.strip()}%"),
        )
        .limit(limit)
    )
    return {
        "users": [
            projection(user) | {"member_id": str(member_id)}
            for user, member_id in (await session.execute(query)).all()
        ]
    }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/users/{user_id}

### Purpose

Get Profile

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
    "name": "user_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "User Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/users/{user_id}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:451](../../../services\user-service\app\main.py). Dependencies: app.auth.require_authenticated_context, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x000002D0BC83CD70>, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/users/{user_id}")
async def get_profile(
    user_id: uuid.UUID,
    context: AuthContext = Depends(require_authenticated_context),
    session: AsyncSession = Depends(db),
):
    target = await session.get(User, user_id)
    if target is None:
        raise HTTPException(404, "user not found")
    if target.identity_id != context.identity_id:
        visible = await session.scalar(
            select(MembershipProjection.id).where(
                MembershipProjection.organization_id == context.organization_id,
                MembershipProjection.user_id == target.id,
                MembershipProjection.status == "ACTIVE",
            )
        )
        if visible is None:
            raise HTTPException(404, "user not found")
    return projection(target)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /internal/v1/users/company-owner

### Purpose

Provision Owner

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

| Field | Required | Type / constraints |
|---|---|---|
| `identity_id` | YES | `{"type": "string", "format": "uuid"}` |
| `display_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 1}` |

```json
{
  "properties": {
    "identity_id": {
      "type": "string",
      "format": "uuid",
      "title": "Identity Id"
    },
    "display_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Display Name"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "identity_id",
    "display_name"
  ],
  "title": "OwnerProvision"
}
```

### Postman Request

`POST http://127.0.0.1:8002/internal/v1/users/company-owner`

```json
{
  "identity_id": "{{replace_with_actual_uuid}}",
  "display_name": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:479](../../../services\user-service\app\main.py). Dependencies: app.main.internal, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/internal/v1/users/provision", dependencies=[Depends(internal)])
@app.post("/internal/v1/users/company-owner", dependencies=[Depends(internal)])
async def provision_owner(body: OwnerProvision, session: AsyncSession = Depends(db)):
    async with session.begin():
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": body.identity_id.int % (2**63 - 1)}
        )
        user = await session.scalar(select(User).where(User.identity_id == body.identity_id))
        if user is None:
            user = User(
                id=body.identity_id, identity_id=body.identity_id, display_name=body.display_name
            )
            session.add(user)
            await session.flush()
            session.add(UserPreferences(user_id=user.id))
            session.add(UserPrivacySettings(user_id=user.id))
            outbox(
                session,
                user,
                "user.created.v1",
                {"display_name": user.display_name, "status": "ACTIVE"},
            )
        # Redelivery never resets a subsequently edited profile.
        return {"user_id": str(user.id)}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /internal/v1/users/provision

### Purpose

Provision Owner

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

| Field | Required | Type / constraints |
|---|---|---|
| `identity_id` | YES | `{"type": "string", "format": "uuid"}` |
| `display_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 1}` |

```json
{
  "properties": {
    "identity_id": {
      "type": "string",
      "format": "uuid",
      "title": "Identity Id"
    },
    "display_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Display Name"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "identity_id",
    "display_name"
  ],
  "title": "OwnerProvision"
}
```

### Postman Request

`POST http://127.0.0.1:8002/internal/v1/users/provision`

```json
{
  "identity_id": "{{replace_with_actual_uuid}}",
  "display_name": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `USER-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\user-service\app\main.py:479](../../../services\user-service\app\main.py). Dependencies: app.main.internal, app.main.db.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/internal/v1/users/provision", dependencies=[Depends(internal)])
@app.post("/internal/v1/users/company-owner", dependencies=[Depends(internal)])
async def provision_owner(body: OwnerProvision, session: AsyncSession = Depends(db)):
    async with session.begin():
        await session.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": body.identity_id.int % (2**63 - 1)}
        )
        user = await session.scalar(select(User).where(User.identity_id == body.identity_id))
        if user is None:
            user = User(
                id=body.identity_id, identity_id=body.identity_id, display_name=body.display_name
            )
            session.add(user)
            await session.flush()
            session.add(UserPreferences(user_id=user.id))
            session.add(UserPrivacySettings(user_id=user.id))
            outbox(
                session,
                user,
                "user.created.v1",
                {"display_name": user.display_name, "status": "ACTIVE"},
            )
        # Redelivery never resets a subsequently edited profile.
        return {"user_id": str(user.id)}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: .

Literal event types in implementation/tests: `identity.created.v1`, `member.activated.v1`, `member.removed.v1`, `member.suspended.v1`, `organization.suspended.v1`, `user.blocked.v1`, `user.created.v1`, `user.preferences_updated.v1`, `user.privacy_updated.v1`, `user.profile_updated.v1`, `user.unblocked.v1`.

Configuration field names (values omitted): .

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\user-service\alembic\versions\0001_initial.py](../../../services/user-service/alembic/versions/0001_initial.py)
- [services\user-service\alembic\versions\0002_outbox_delivery_state.py](../../../services/user-service/alembic/versions/0002_outbox_delivery_state.py)
- [services\user-service\app\auth.py](../../../services/user-service/app/auth.py)
- [services\user-service\app\consumer_runner.py](../../../services/user-service/app/consumer_runner.py)
- [services\user-service\app\outbox_runner.py](../../../services/user-service/app/outbox_runner.py)
- [services\user-service\tests\contracts\test_events.py](../../../services/user-service/tests/contracts/test_events.py)
- [services\user-service\tests\contracts\test_workspace_people.py](../../../services/user-service/tests/contracts/test_workspace_people.py)
- [services\user-service\tests\integration\test_company_owner.py](../../../services/user-service/tests/integration/test_company_owner.py)
- [services\user-service\tests\security\test_internal_auth.py](../../../services/user-service/tests/security/test_internal_auth.py)
- [services\user-service\tests\security\test_jwt_security.py](../../../services/user-service/tests/security/test_jwt_security.py)
- [services\user-service\tests\security\test_tenant_privacy_behavior.py](../../../services/user-service/tests/security/test_tenant_privacy_behavior.py)
- [services\user-service\tests\unit\test_auth.py](../../../services/user-service/tests/unit/test_auth.py)
- [services\user-service\tests\unit\test_health.py](../../../services/user-service/tests/unit/test_health.py)
- [services\user-service\tests\unit\test_outbox_publisher.py](../../../services/user-service/tests/unit/test_outbox_publisher.py)
- [services\user-service\tests\unit\test_rabbitmq_consumer.py](../../../services/user-service/tests/unit/test_rabbitmq_consumer.py)
- [services\user-service\tests\unit\test_user_api_routes.py](../../../services/user-service/tests/unit/test_user_api_routes.py)
- [services\user-service\tests\unit\test_user_event_consumers.py](../../../services/user-service/tests/unit/test_user_event_consumers.py)
# Platform administration relevance

No platform-user endpoint exists in C1. Current routes remain authenticated tenant/self-profile contracts and must not be used for cross-tenant administration. Profile privacy and block policy remain authoritative.


## Personal self-service context

Valid Identity personal JWTs may omit org/mid together. Self profile/preferences/privacy remain available; partial tenant claims are rejected. Personal /users/search returns 403 and arbitrary other-user profile lookup returns 404. Contact matching is not implemented.


## Personal contact discovery

Authenticated `/api/v1/contacts` CRUD and `/api/v1/contacts/match` route through Gateway to User. See [contact contracts, limits and privacy](../CONTACT-DISCOVERY.md). Contacts require user ownership, not company membership.
