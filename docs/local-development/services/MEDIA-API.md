# Media Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | media |
| Framework | FastAPI |
| Local Port | 8005 |
| Base URL | http://127.0.0.1:8005 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8005/openapi.json |
| Health URL | http://127.0.0.1:8005/health/ready |
| PostgreSQL database | teamchat_media_db |
| Redis | Runner endpoint 127.0.0.1:6380/0; actual dependencies in source below |
| RabbitMQ | Runner endpoint 127.0.0.1:5672, vhost `/`; actual workers below |

## Authentication

Health routes are public. Product routes use Identity-issued RS256 tokens and actual service-specific authorization. Internal routes require a service token and are operator-only. Public challenge routes require their documented challenge/OTP/refresh proof. Tenant context is derived from verified tokens; there is no invented X-Organization-ID requirement. Organization permission codes are checked against current tenant role assignments, not merely a frontend role label. See [permission defaults](../../../services/organization-service/common/authorization.py).

## Required Headers

JSON requests: `Content-Type: application/json`. Bearer routes: `Authorization: Bearer {{access_token}}`. Internal routes: `X-Internal-Service-Token: {{internal_service_token}}`. Additional parameters below are from actual schemas. Never attach credentials to signed storage URLs.

## Route Summary

| # | Method | Route | Auth | Role / permission | Purpose |
|---|---|---|---|---|---|
| 1 | PUT | `/local-storage/{token}` | Signed capability in URL | `No fixed application role` | local put |
| 2 | GET | `/local-storage/{token}` | Signed capability in URL | `No fixed application role` | local get |
| 3 | GET | `/health/live` | None at this layer | `No fixed application role` | live |
| 4 | GET | `/health/ready` | None at this layer | `No fixed application role` | ready |
| 5 | POST | `/api/v1/media/uploads` | Bearer access token | `Resource membership/ownership checks; see handler` | initiate upload |
| 6 | POST | `/api/v1/media/multipart` | Bearer access token | `Resource membership/ownership checks; see handler` | initiate multipart |
| 7 | POST | `/api/v1/media/{media_id}/multipart/parts` | Bearer access token | `Resource membership/ownership checks; see handler` | multipart parts |
| 8 | GET | `/api/v1/media/{media_id}/multipart` | Bearer access token | `Resource membership/ownership checks; see handler` | multipart resume |
| 9 | POST | `/api/v1/media/{media_id}/multipart/complete` | Bearer access token | `Resource membership/ownership checks; see handler` | complete multipart |
| 10 | DELETE | `/api/v1/media/{media_id}/multipart` | Bearer access token | `Resource membership/ownership checks; see handler` | abort multipart |
| 11 | POST | `/api/v1/media/{media_id}/complete` | Bearer access token | `Resource membership/ownership checks; see handler` | complete upload |
| 12 | GET | `/api/v1/media/{media_id}/download` | Bearer access token | `Resource membership/ownership checks; see handler` | download |
| 13 | DELETE | `/api/v1/media/{media_id}` | Bearer access token | `Resource membership/ownership checks; see handler` | delete |

## PUT /local-storage/{token}

### Purpose

local put

### Authentication

Required: YES. Token: Signed capability in URL. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

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

`PUT http://127.0.0.1:8005/local-storage/{token}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:67](../../../services\media-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.put("/local-storage/{token}", include_in_schema=False)
    async def local_put(token: str, request: Request):
        import hashlib
        import json
        import os

        from app.storage import StorageError

        storage = service().storage
        try:
            body = storage.verify(token, "put")
        except StorageError:
            try:
                body = storage.verify(token, "part")
            except StorageError:
                return JSONResponse({"error": "invalid storage capability"}, status_code=403)
        path = storage.location(body["bucket"], body["key"])
        if body["action"] == "part":
            path = (
                storage.parts_path(body["bucket"], body["key"], body["upload_id"])
                / f"{int(body['part_number'])}.part"
            )
        elif request.headers.get("content-type") != body["mime"]:
            return JSONResponse({"error": "content type mismatch"}, status_code=400)
        temporary = path.with_suffix(".uploading")
        size = 0
        digest = hashlib.sha256()
        try:
            with temporary.open("wb") as handle:
                async for chunk in request.stream():
                    size += len(chunk)
                    if size > 64 * 1024 * 1024:
                        return JSONResponse(
                            {"error": "local part limit is 64 MiB; use multipart"}, status_code=413
                        )
                    digest.update(chunk)
                    handle.write(chunk)
            os.replace(temporary, path)
            if body["action"] == "put":
                path.with_suffix(".json").write_text(json.dumps({"mime": body["mime"]}))
            return JSONResponse({"status": "uploaded"}, headers={"ETag": digest.hexdigest()})
        finally:
            temporary.unlink(missing_ok=True)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /local-storage/{token}

### Purpose

local get

### Authentication

Required: YES. Token: Signed capability in URL. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

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

`GET http://127.0.0.1:8005/local-storage/{token}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:111](../../../services\media-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.get("/local-storage/{token}", include_in_schema=False)
    async def local_get(token: str):
        from fastapi.responses import FileResponse

        from app.storage import StorageError

        storage = service().storage
        try:
            body = storage.verify(token, "get")
        except StorageError:
            return JSONResponse({"error": "invalid storage capability"}, status_code=403)
        metadata = await storage.head(body["bucket"], body["key"])
        if metadata is None:
            return JSONResponse({"error": "object unavailable"}, status_code=404)
        return FileResponse(
            storage.location(body["bucket"], body["key"]), media_type=metadata.mime_type
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

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

`GET http://127.0.0.1:8005/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:134](../../../services\media-service\app\main.py). Dependencies: See middleware/handler.

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

`GET http://127.0.0.1:8005/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:139](../../../services\media-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready", tags=["health"])
async def ready():
    from sqlalchemy import text

    try:
        if isinstance(service(), DurableMediaService):
            async with SessionLocal() as session:
                await session.execute(text("SELECT 1"))
        storage_ready = await service().storage.ready()
    except Exception:
        storage_ready = False
    if storage_ready:
        response = {"status": "ready", "storage": "available"}
        if isinstance(service(), DurableMediaService):
            response["database"] = "available"
        return response
    return JSONResponse(status_code=503, content={"status": "not_ready", "storage": "unavailable"})
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/media/uploads

### Purpose

Initiate Upload

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
| `conversation_id` | YES | `{"type": "string", "format": "uuid"}` |
| `filename` | YES | `{"type": "string", "maxLength": 512, "minLength": 1}` |
| `mime_type` | YES | `{"type": "string"}` |
| `size_bytes` | YES | `{"type": "integer", "exclusiveMinimum": 0.0}` |
| `media_type` | YES | `{"type": "string"}` |
| `checksum_sha256` | NO | `{"anyOf": [{"type": "string", "pattern": "^[a-fA-F0-9]{64}$"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "conversation_id": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    },
    "filename": {
      "type": "string",
      "maxLength": 512,
      "minLength": 1,
      "title": "Filename"
    },
    "mime_type": {
      "type": "string",
      "title": "Mime Type"
    },
    "size_bytes": {
      "type": "integer",
      "exclusiveMinimum": 0.0,
      "title": "Size Bytes"
    },
    "media_type": {
      "type": "string",
      "title": "Media Type"
    },
    "checksum_sha256": {
      "anyOf": [
        {
          "type": "string",
          "pattern": "^[a-fA-F0-9]{64}$"
        },
        {
          "type": "null"
        }
      ],
      "title": "Checksum Sha256"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "conversation_id",
    "filename",
    "mime_type",
    "size_bytes",
    "media_type"
  ],
  "title": "UploadRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/media/uploads`

```json
{
  "conversation_id": "{{replace_with_actual_uuid}}",
  "filename": "{{replace_with_valid_value}}",
  "mime_type": "{{replace_with_valid_value}}",
  "size_bytes": 1,
  "media_type": "{{replace_with_valid_value}}",
  "checksum_sha256": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:158](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/media/uploads", status_code=201)
async def initiate_upload(
    request: UploadRequest, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().initiate(
        principal, request, http_request.headers.get("X-Correlation-ID", "")
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/media/multipart

### Purpose

Initiate Multipart

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
| `conversation_id` | YES | `{"type": "string", "format": "uuid"}` |
| `filename` | YES | `{"type": "string", "maxLength": 512, "minLength": 1}` |
| `mime_type` | YES | `{"type": "string"}` |
| `size_bytes` | YES | `{"type": "integer", "exclusiveMinimum": 0.0}` |
| `media_type` | YES | `{"type": "string"}` |
| `checksum_sha256` | NO | `{"anyOf": [{"type": "string", "pattern": "^[a-fA-F0-9]{64}$"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "conversation_id": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    },
    "filename": {
      "type": "string",
      "maxLength": 512,
      "minLength": 1,
      "title": "Filename"
    },
    "mime_type": {
      "type": "string",
      "title": "Mime Type"
    },
    "size_bytes": {
      "type": "integer",
      "exclusiveMinimum": 0.0,
      "title": "Size Bytes"
    },
    "media_type": {
      "type": "string",
      "title": "Media Type"
    },
    "checksum_sha256": {
      "anyOf": [
        {
          "type": "string",
          "pattern": "^[a-fA-F0-9]{64}$"
        },
        {
          "type": "null"
        }
      ],
      "title": "Checksum Sha256"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "conversation_id",
    "filename",
    "mime_type",
    "size_bytes",
    "media_type"
  ],
  "title": "UploadRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/media/multipart`

```json
{
  "conversation_id": "{{replace_with_actual_uuid}}",
  "filename": "{{replace_with_valid_value}}",
  "mime_type": "{{replace_with_valid_value}}",
  "size_bytes": 1,
  "media_type": "{{replace_with_valid_value}}",
  "checksum_sha256": "{{replace_with_valid_value}}"
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:167](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/media/multipart", status_code=201)
async def initiate_multipart(
    request: UploadRequest, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().initiate_multipart(
        principal, request, http_request.headers.get("X-Correlation-ID", "")
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/media/{media_id}/multipart/parts

### Purpose

Multipart Parts

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

| Field | Required | Type / constraints |
|---|---|---|
| `part_numbers` | YES | `{"type": "array", "maxItems": 25, "minItems": 1}` |

```json
{
  "properties": {
    "part_numbers": {
      "items": {
        "type": "integer"
      },
      "type": "array",
      "maxItems": 25,
      "minItems": 1,
      "title": "Part Numbers"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "part_numbers"
  ],
  "title": "MultipartPartsRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/media/{media_id}/multipart/parts`

```json
{
  "part_numbers": [
    1
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:176](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/media/{media_id}/multipart/parts")
async def multipart_parts(
    media_id: UUID,
    request: MultipartPartsRequest,
    principal: Principal = Depends(get_principal),
):
    return await service().multipart_part_urls(principal, media_id, request.part_numbers)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/media/{media_id}/multipart

### Purpose

Multipart Resume

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

`GET http://localhost:8008/api/v1/media/{media_id}/multipart`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:185](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/media/{media_id}/multipart")
async def multipart_resume(media_id: UUID, principal: Principal = Depends(get_principal)):
    return await service().multipart_status(principal, media_id)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/media/{media_id}/multipart/complete

### Purpose

Complete Multipart

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

| Field | Required | Type / constraints |
|---|---|---|
| `parts` | YES | `{"type": "array", "maxItems": 10000, "minItems": 1}` |

```json
{
  "properties": {
    "parts": {
      "items": {
        "additionalProperties": true,
        "type": "object"
      },
      "type": "array",
      "maxItems": 10000,
      "minItems": 1,
      "title": "Parts"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "parts"
  ],
  "title": "MultipartCompleteRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/media/{media_id}/multipart/complete`

```json
{
  "parts": [
    {}
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:190](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/media/{media_id}/multipart/complete")
async def complete_multipart(
    media_id: UUID,
    request: MultipartCompleteRequest,
    http_request: Request,
    principal: Principal = Depends(get_principal),
):
    return await service().complete_multipart(
        principal, media_id, request.parts, http_request.headers.get("X-Correlation-ID", "")
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/media/{media_id}/multipart

### Purpose

Abort Multipart

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

`DELETE http://localhost:8008/api/v1/media/{media_id}/multipart`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:202](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/media/{media_id}/multipart")
async def abort_multipart(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    await service().abort_multipart(
        principal, media_id, http_request.headers.get("X-Correlation-ID", "")
    )
    return {"status": "aborted"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/media/{media_id}/complete

### Purpose

Complete Upload

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

`POST http://localhost:8008/api/v1/media/{media_id}/complete`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:212](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.post("/api/v1/media/{media_id}/complete")
async def complete_upload(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    return await service().complete(
        principal, media_id, http_request.headers.get("X-Correlation-ID", "")
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/media/{media_id}/download

### Purpose

Download

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

`GET http://localhost:8008/api/v1/media/{media_id}/download`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:221](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/api/v1/media/{media_id}/download")
async def download(media_id: UUID, principal: Principal = Depends(get_principal)):
    return {"download_url": await service().download(principal, media_id)}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /api/v1/media/{media_id}

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
    "name": "media_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Media Id"
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

`DELETE http://localhost:8008/api/v1/media/{media_id}`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `MEDIA-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\media-service\app\main.py:226](../../../services\media-service\app\main.py). Dependencies: app.security.get_principal.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.delete("/api/v1/media/{media_id}")
async def delete(
    media_id: UUID, http_request: Request, principal: Principal = Depends(get_principal)
):
    await service().delete(principal, media_id, http_request.headers.get("X-Correlation-ID", ""))
    return {"status": "deleted"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: .

Literal event types in implementation/tests: `media.deleted.v1`, `media.failed.v1`, `media.ready.v1`, `message.created.v1`, `message.deleted.v1`.

Configuration field names (values omitted): `allowed`, `app_env`, `aws_region`, `bucket`, `conversation_api_url`, `database_url`, `jwt_algorithm`, `jwt_audience`, `jwt_issuer`, `jwt_public_key`, `local_storage_base_url`, `local_storage_root`, `local_storage_secret`, `max_upload_size_bytes`, `maximum`, `media_s3_bucket`, `media_s3_endpoint_url`, `media_storage_backend`, `multipart_max_parts`, `multipart_part_size_bytes`, `multipart_threshold_bytes`, `multipart_url_batch_limit`, `pending_ttl_seconds`, `upload_ttl_seconds`.

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\media-service\alembic\versions\0001_media_schema.py](../../../services/media-service/alembic/versions/0001_media_schema.py)
- [services\media-service\alembic\versions\0002_usage_reserved_bytes.py](../../../services/media-service/alembic/versions/0002_usage_reserved_bytes.py)
- [services\media-service\app\config.py](../../../services/media-service/app/config.py)
- [services\media-service\app\consumer_runner.py](../../../services/media-service/app/consumer_runner.py)
- [services\media-service\app\models.py](../../../services/media-service/app/models.py)
- [services\media-service\app\outbox_runner.py](../../../services/media-service/app/outbox_runner.py)
- [services\media-service\app\schemas.py](../../../services/media-service/app/schemas.py)
- [services\media-service\app\security.py](../../../services/media-service/app/security.py)
- [services\media-service\tests\contracts\test_contracts.py](../../../services/media-service/tests/contracts/test_contracts.py)
- [services\media-service\tests\security\test_conversation_access.py](../../../services/media-service/tests/security/test_conversation_access.py)
- [services\media-service\tests\security\test_media_security.py](../../../services/media-service/tests/security/test_media_security.py)
- [services\media-service\tests\security\test_multipart_security.py](../../../services/media-service/tests/security/test_multipart_security.py)
- [services\media-service\tests\unit\test_durable_media.py](../../../services/media-service/tests/unit/test_durable_media.py)
- [services\media-service\tests\unit\test_local_storage.py](../../../services/media-service/tests/unit/test_local_storage.py)
- [services\media-service\tests\unit\test_media_service.py](../../../services/media-service/tests/unit/test_media_service.py)
- [services\media-service\tests\unit\test_multipart.py](../../../services/media-service/tests/unit/test_multipart.py)
- [services\media-service\tests\unit\test_s3_storage.py](../../../services/media-service/tests/unit/test_s3_storage.py)
# Platform administration relevance

No platform media metadata route exists in C1. Upload/download signing remains tenant-authorized and private media bytes and signatures are excluded from administration.

