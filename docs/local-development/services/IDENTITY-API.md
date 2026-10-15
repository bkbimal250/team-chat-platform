# Identity Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | identity |
| Framework | FastAPI |
| Local Port | 8001 |
| Base URL | http://127.0.0.1:8001 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8001/api/schema/ |
| Health URL | http://127.0.0.1:8001/health/ready |
| PostgreSQL database | identity_db |
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
| 3 | POST | `/api/v1/auth/otp/request` | No bearer; challenge/refresh proof where required | `No fixed application role` | otp request |
| 4 | POST | `/api/v1/auth/otp/verify` | No bearer; challenge/refresh proof where required | `No fixed application role` | otp verify |
| 5 | POST | `/api/v1/auth/refresh` | No bearer; challenge/refresh proof where required | `No fixed application role` | refresh |
| 6 | POST | `/api/v1/auth/logout` | Bearer access token | `Resource membership/ownership checks; see handler` | logout |
| 7 | POST | `/api/v1/auth/logout-all` | Bearer access token | `Resource membership/ownership checks; see handler` | logout all |
| 8 | POST | `/api/v1/auth/context` | Bearer access token | `Resource membership/ownership checks; see handler` | switch context |
| 9 | GET | `/api/v1/auth/me` | Bearer access token | `Resource membership/ownership checks; see handler` | me |
| 10 | POST | `/api/v1/auth/qr/challenges` | No bearer; challenge/refresh proof where required | `No fixed application role` | qr create |
| 11 | GET | `/api/v1/auth/qr/challenges/{challenge_id}/status` | No bearer; challenge/refresh proof where required | `No fixed application role` | qr status |
| 12 | POST | `/api/v1/auth/qr/challenges/{challenge_id}/authorize` | Bearer access token | `Resource membership/ownership checks; see handler` | qr authorize |
| 13 | POST | `/api/v1/auth/qr/challenges/{challenge_id}/consume` | No bearer; challenge/refresh proof where required | `No fixed application role` | qr consume |
| 14 | POST | `/api/v1/auth/login` | No bearer; challenge/refresh proof where required | `No fixed application role` | login |
| 15 | POST | `/api/v1/auth/registration/company` | No bearer; challenge/refresh proof where required | `No fixed application role` | register |
| 16 | POST | `/api/v1/auth/invitations/password` | No bearer; challenge/refresh proof where required | `No fixed application role` | invitation password |
| 17 | POST | `/api/v1/auth/registration/company/start` | No bearer; challenge/refresh proof where required | `No fixed application role` | start |
| 18 | POST | `/api/v1/auth/registration/company/resend` | No bearer; challenge/refresh proof where required | `No fixed application role` | resend |
| 19 | POST | `/api/v1/auth/registration/company/verify` | No bearer; challenge/refresh proof where required | `No fixed application role` | verify |
| 20 | POST | `/api/v1/auth/invitations/validate` | No bearer; challenge/refresh proof where required | `No fixed application role` | validate |
| 21 | POST | `/api/v1/auth/invitations/resend` | No bearer; challenge/refresh proof where required | `No fixed application role` | request otp |
| 22 | POST | `/api/v1/auth/invitations/request` | No bearer; challenge/refresh proof where required | `No fixed application role` | request otp |
| 23 | POST | `/api/v1/auth/invitations/verify` | No bearer; challenge/refresh proof where required | `No fixed application role` | verify |
| 24 | GET | `/api/v1/devices` | Bearer access token | `Resource membership/ownership checks; see handler` | devices |
| 25 | GET | `/api/v1/devices/{device_id}` | Bearer access token | `Resource membership/ownership checks; see handler` | device |
| 26 | POST | `/api/v1/devices/{device_id}/revoke` | Bearer access token | `Resource membership/ownership checks; see handler` | revoke device |
| 27 | GET | `/api/v1/auth/sessions` | Bearer access token | `Resource membership/ownership checks; see handler` | sessions |
| 28 | POST | `/api/v1/auth/sessions/{session_id}/revoke` | Bearer access token | `Resource membership/ownership checks; see handler` | revoke |

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

`GET http://127.0.0.1:8001/health/live`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\main.py:105](../../../services\identity-service\app\main.py). Dependencies: See middleware/handler.

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

`GET http://127.0.0.1:8001/health/ready`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\main.py:110](../../../services\identity-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@app.get("/health/ready", tags=["health"])
async def ready(request: Request):
    try:
        async with SessionLocal() as db:
            await db.execute(text("SELECT 1"))
        await request.app.state.redis.ping()
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return {
        "status": "ready",
        "database": "available",
        "redis": "available",
        "broker": "asynchronous; monitored by outbox worker",
    }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/otp/request

### Purpose

Otp Request

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `phone_number` | YES | `{"type": "string", "maxLength": 64}` |
| `purpose` | YES | `{"type": "string", "pattern": "^(LOGIN|REGISTER|PHONE_VERIFY|RECOVERY)$"}` |

```json
{
  "properties": {
    "phone_number": {
      "type": "string",
      "maxLength": 64,
      "title": "Phone Number"
    },
    "purpose": {
      "type": "string",
      "pattern": "^(LOGIN|REGISTER|PHONE_VERIFY|RECOVERY)$",
      "title": "Purpose"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "phone_number",
    "purpose"
  ],
  "title": "OTPRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/otp/request`

```json
{
  "phone_number": "{{replace_with_valid_value}}",
  "purpose": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "202": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/OTPRequestResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:80](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/otp/request", response_model=OTPRequestResponse, status_code=202)
async def otp_request(
    payload: OTPRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, _ = context(request)
    async with command_transaction(db):
        challenge, development_code = await otp_service(request).request(
            db, payload.phone_number, payload.purpose, client_ip(request), correlation_id
        )
    # Returning a challenge id is not identity enumeration; response body stays otherwise generic.
    return OTPRequestResponse(challenge_id=challenge.id, development_code=development_code)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/otp/verify

### Purpose

Otp Verify

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `challenge_id` | YES | `{"type": "string", "format": "uuid"}` |
| `code` | YES | `{"type": "string", "pattern": "^\\d{6}$"}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |
| `organization_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "challenge_id": {
      "type": "string",
      "format": "uuid",
      "title": "Challenge Id"
    },
    "code": {
      "type": "string",
      "pattern": "^\\d{6}$",
      "title": "Code"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    },
    "organization_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Organization Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "challenge_id",
    "code",
    "device"
  ],
  "title": "OTPVerifyRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/otp/verify`

```json
{
  "challenge_id": "{{replace_with_actual_uuid}}",
  "code": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  },
  "organization_id": "{{replace_with_actual_uuid}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:93](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/otp/verify", response_model=TokenResponse)
async def otp_verify(
    payload: OTPVerifyRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    async with command_transaction(db):
        challenge = await otp_service(request).verify(
            db, payload.challenge_id, payload.code, client_ip(request), correlation_id
        )
        identity = (
            await db.execute(
                select(Identity)
                .where(Identity.phone_number == challenge.phone_number)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if identity is None:
            if get_settings().registration_policy == "INVITE_ONLY":
                raise DomainError("REGISTRATION_NOT_ALLOWED", "Authentication is unavailable.", 403)
            identity = Identity(
                phone_number=challenge.phone_number,
                phone_verified=True,
                status=IdentityStatus.ACTIVE,
            )
            db.add(identity)
            await db.flush()
            await audit_and_event(
                db,
                action="IDENTITY_CREATED",
                event_type="identity.created.v1",
                aggregate_type="identity",
                aggregate_id=identity.id,
                correlation_id=correlation_id,
                identity_id=identity.id,
                ip_address=client_ip(request),
            )
        if identity.status != IdentityStatus.ACTIVE:
            raise DomainError("IDENTITY_INACTIVE", "Authentication is unavailable.", 403)
        memberships = await OrganizationServiceClient().memberships(identity.id, correlation_id)
        active = [item for item in memberships if item.status == "ACTIVE"]
        if payload.organization_id:
            active = [item for item in active if item.organization_id == payload.organization_id]
        if not active:
            raise DomainError(
                "MEMBERSHIP_INACTIVE", "No active organization membership is available.", 403
            )
        selected = active[0]
        sessions = SessionService()
        device = await sessions.device(db, identity.id, payload.device)
        return await sessions.create(
            db,
            identity=identity,
            device=device,
            organization_id=selected.organization_id,
            member_id=selected.member_id,
            ip=client_ip(request),
            user_agent=user_agent,
            correlation_id=correlation_id,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/refresh

### Purpose

Refresh

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `refresh_token` | YES | `{"type": "string", "maxLength": 512, "minLength": 32}` |

```json
{
  "properties": {
    "refresh_token": {
      "type": "string",
      "maxLength": 512,
      "minLength": 32,
      "title": "Refresh Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "refresh_token"
  ],
  "title": "RefreshRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/refresh`

```json
{
  "refresh_token": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:154](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/refresh", response_model=TokenResponse)
async def refresh(
    payload: RefreshRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(f"refresh:ip:{client_ip(request)}", 60, 3600)
    correlation_id, user_agent = context(request)
    async with command_transaction(db):
        return await SessionService().refresh(
            db, payload.refresh_token, client_ip(request), user_agent, correlation_id
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/logout

### Purpose

Logout

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

`POST http://localhost:8008/api/v1/auth/logout`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:166](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/logout", response_model=RevokeResponse)
async def logout(
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    async with command_transaction(db):
        await SessionService().revoke_session(
            db, principal.session, request.state.correlation_id, client_ip(request)
        )
    return RevokeResponse(status="REVOKED")
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/logout-all

### Purpose

Revokes all sessions, including the current session; clients must clear all credentials.

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

`POST http://localhost:8008/api/v1/auth/logout-all`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:179](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/logout-all", response_model=RevokeResponse)
async def logout_all(
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    """Revokes all sessions, including the current session; clients must clear all credentials."""
    async with command_transaction(db):
        rows = (
            (
                await db.execute(
                    select(Session)
                    .where(
                        Session.identity_id == principal.identity_id,
                        Session.status == SessionStatus.ACTIVE,
                    )
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        service = SessionService()
        for row in rows:
            await service.revoke_session(
                db, row, request.state.correlation_id, client_ip(request), "LOGOUT_ALL"
            )
    return RevokeResponse(status="REVOKED")
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/context

### Purpose

Switch Context

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
| `organization_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "properties": {
    "organization_id": {
      "type": "string",
      "format": "uuid",
      "title": "Organization Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "organization_id"
  ],
  "title": "ContextRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/context`

```json
{
  "organization_id": "{{replace_with_actual_uuid}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:209](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/context", response_model=TokenResponse)
async def switch_context(
    payload: ContextRequest,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    correlation_id, user_agent = context(request)
    membership = [
        item
        for item in await OrganizationServiceClient().memberships(
            principal.identity_id, correlation_id
        )
        if item.organization_id == payload.organization_id and item.status == "ACTIVE"
    ]
    if not membership:
        raise DomainError(
            "MEMBERSHIP_INACTIVE", "The requested organization context is unavailable.", 403
        )
    identity = (
        await db.execute(select(Identity).where(Identity.id == principal.identity_id))
    ).scalar_one()
    async with command_transaction(db):
        return await SessionService().create(
            db,
            identity=identity,
            device=principal.device,
            organization_id=membership[0].organization_id,
            member_id=membership[0].member_id,
            ip=client_ip(request),
            user_agent=user_agent,
            correlation_id=correlation_id,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/auth/me

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

`GET http://localhost:8008/api/v1/auth/me`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/MeResponse"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:244](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("/me", response_model=MeResponse)
async def me(principal: Principal = Depends(current_principal)):
    return MeResponse(
        identity={"id": principal.identity_id},
        session={"id": principal.session.id, "device_id": principal.device.id},
        context={
            "organization_id": principal.session.organization_id,
            "member_id": principal.session.member_id,
        },
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/qr/challenges

### Purpose

Qr Create

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `installation_id` | YES | `{"type": "string", "maxLength": 256, "minLength": 16}` |
| `platform` | YES | `{"type": "string", "enum": ["ANDROID", "IOS", "WEB"]}` |
| `device_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 1}` |
| `device_model` | NO | `{"anyOf": [{"type": "string", "maxLength": 200}, {"type": "null"}]}` |
| `os_version` | NO | `{"anyOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}` |
| `app_version` | NO | `{"anyOf": [{"type": "string", "maxLength": 100}, {"type": "null"}]}` |

```json
{
  "properties": {
    "installation_id": {
      "type": "string",
      "maxLength": 256,
      "minLength": 16,
      "title": "Installation Id"
    },
    "platform": {
      "$ref": "#/components/schemas/DevicePlatform"
    },
    "device_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 1,
      "title": "Device Name"
    },
    "device_model": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 200
        },
        {
          "type": "null"
        }
      ],
      "title": "Device Model"
    },
    "os_version": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 100
        },
        {
          "type": "null"
        }
      ],
      "title": "Os Version"
    },
    "app_version": {
      "anyOf": [
        {
          "type": "string",
          "maxLength": 100
        },
        {
          "type": "null"
        }
      ],
      "title": "App Version"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "installation_id",
    "platform",
    "device_name"
  ],
  "title": "QRCreateRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/qr/challenges`

```json
{
  "installation_id": "{{replace_with_valid_value}}",
  "platform": "ANDROID",
  "device_name": "{{replace_with_valid_value}}",
  "device_model": "{{replace_with_valid_value}}",
  "os_version": "{{replace_with_valid_value}}",
  "app_version": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/QRCreateResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:256](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/qr/challenges", response_model=QRCreateResponse, status_code=201)
async def qr_create(
    payload: QRCreateRequest, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(f"qr:create:{payload.installation_id}", 10, 3600)
    async with command_transaction(db):
        return await QRService(SessionService()).create(
            db, payload, request.state.correlation_id, client_ip(request)
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/auth/qr/challenges/{challenge_id}/status

### Purpose

Qr Status

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
(No additional application header required.)
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "challenge_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Challenge Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/auth/qr/challenges/{challenge_id}/status`

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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:267](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("/qr/challenges/{challenge_id}/status")
async def qr_status(challenge_id: UUID, request: Request, db: AsyncSession = Depends(get_session)):
    await RateLimiter(request.app.state.redis).hit(
        f"qr:poll:{client_ip(request)}:{challenge_id}", 60, 60
    )
    async with command_transaction(db):
        challenge = await QRService(SessionService()).locked(db, challenge_id)
        return {
            "challenge_id": challenge.public_challenge_id,
            "status": challenge.status,
            "expires_at": challenge.expires_at,
        }
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/qr/challenges/{challenge_id}/authorize

### Purpose

Qr Authorize

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
    "name": "challenge_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Challenge Id"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `secret` | YES | `{"type": "string", "maxLength": 512, "minLength": 32}` |

```json
{
  "properties": {
    "secret": {
      "type": "string",
      "maxLength": 512,
      "minLength": 32,
      "title": "Secret"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "secret"
  ],
  "title": "QRAuthorizeRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/qr/challenges/{challenge_id}/authorize`

```json
{
  "secret": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:281](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/qr/challenges/{challenge_id}/authorize", response_model=RevokeResponse)
async def qr_authorize(
    challenge_id: UUID,
    payload: QRAuthorizeRequest,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    await RateLimiter(request.app.state.redis).hit(
        f"qr:authorize:{principal.identity_id}", 30, 3600
    )
    async with command_transaction(db):
        await QRService(SessionService()).authorize(
            db,
            challenge_id,
            payload.secret,
            principal.session,
            request.state.correlation_id,
            client_ip(request),
        )
    return RevokeResponse(status="AUTHORIZED")
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/qr/challenges/{challenge_id}/consume

### Purpose

Qr Consume

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "challenge_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Challenge Id"
    }
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `secret` | YES | `{"type": "string", "maxLength": 512, "minLength": 32}` |

```json
{
  "properties": {
    "secret": {
      "type": "string",
      "maxLength": 512,
      "minLength": 32,
      "title": "Secret"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "secret"
  ],
  "title": "QRConsumeRequest"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/qr/challenges/{challenge_id}/consume`

```json
{
  "secret": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\auth.py:304](../../../services\identity-service\app\api\v1\auth.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/qr/challenges/{challenge_id}/consume", response_model=TokenResponse)
async def qr_consume(
    challenge_id: UUID,
    payload: QRConsumeRequest,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    correlation_id, user_agent = context(request)
    async with command_transaction(db):
        return await QRService(SessionService()).consume(
            db, challenge_id, payload.secret, client_ip(request), user_agent, correlation_id
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/login

### Purpose

Login

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `email` | YES | `{"type": "string", "maxLength": 320}` |
| `password` | YES | `{"type": "string", "maxLength": 128, "minLength": 1}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |
| `organization_id` | NO | `{"anyOf": [{"type": "string", "format": "uuid"}, {"type": "null"}]}` |

```json
{
  "properties": {
    "email": {
      "type": "string",
      "maxLength": 320,
      "title": "Email"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 1,
      "title": "Password"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    },
    "organization_id": {
      "anyOf": [
        {
          "type": "string",
          "format": "uuid"
        },
        {
          "type": "null"
        }
      ],
      "title": "Organization Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "email",
    "password",
    "device"
  ],
  "title": "PasswordLogin"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/login`

```json
{
  "email": "{{replace_with_valid_value}}",
  "password": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  },
  "organization_id": "{{replace_with_actual_uuid}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\password.py:94](../../../services\identity-service\app\api\v1\password.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/login", response_model=TokenResponse)
async def login(payload: PasswordLogin, request: Request, db: AsyncSession = Depends(get_session)):
    enabled()
    await limits(request, payload.email, "login")
    async with db.begin():
        identity = await db.scalar(
            select(Identity)
            .where(func.lower(func.trim(Identity.email)) == payload.email)
            .with_for_update()
        )
        valid = verify_secret(
            payload.password,
            identity.password_hash if identity and identity.password_hash else DUMMY_HASH,
        )
        if (
            not valid
            or identity is None
            or not identity.password_hash
            or identity.status != IdentityStatus.ACTIVE
        ):
            raise DomainError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
        memberships = await OrganizationServiceClient().memberships(
            identity.id, request.state.correlation_id
        )
        active = [
            m
            for m in memberships
            if m.status == "ACTIVE"
            and (payload.organization_id is None or m.organization_id == payload.organization_id)
        ]
        if not active:
            raise DomainError(
                "MEMBERSHIP_INACTIVE", "No active workspace membership is available.", 403
            )
        return await issue(
            db, identity, payload, active[0].organization_id, active[0].member_id, request
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/registration/company

### Purpose

Register

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `company_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 2}` |
| `owner_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 2}` |
| `email` | YES | `{"type": "string", "maxLength": 254}` |
| `phone` | YES | `{"type": "string", "maxLength": 64}` |
| `password` | YES | `{"type": "string", "maxLength": 128, "minLength": 12}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |

```json
{
  "properties": {
    "company_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 2,
      "title": "Company Name"
    },
    "owner_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 2,
      "title": "Owner Name"
    },
    "email": {
      "type": "string",
      "maxLength": 254,
      "title": "Email"
    },
    "phone": {
      "type": "string",
      "maxLength": 64,
      "title": "Phone"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 12,
      "title": "Password"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "company_name",
    "owner_name",
    "email",
    "phone",
    "password",
    "device"
  ],
  "title": "PasswordRegistration"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/registration/company`

```json
{
  "company_name": "{{replace_with_valid_value}}",
  "owner_name": "{{replace_with_valid_value}}",
  "email": "{{replace_with_valid_value}}",
  "phone": "{{replace_with_valid_value}}",
  "password": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  }
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\password.py:133](../../../services\identity-service\app\api\v1\password.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/registration/company", response_model=TokenResponse, status_code=201)
async def register(
    payload: PasswordRegistration, request: Request, db: AsyncSession = Depends(get_session)
):
    enabled()
    await limits(request, payload.email, "register")
    failure = None
    try:
        async with db.begin():
            # Same canonical email serializes retries and concurrent initial requests.
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": "email:" + payload.email},
            )
            identity = await db.scalar(
                select(Identity)
                .where(func.lower(func.trim(Identity.email)) == payload.email)
                .with_for_update()
            )
            if identity:
                row = await db.scalar(
                    select(CompanyRegistration)
                    .where(CompanyRegistration.identity_id == identity.id)
                    .with_for_update()
                )
                if (
                    row is None
                    or row.challenge_id is not None
                    or row.state == "COMPLETED"
                    or not identity.password_hash
                    or not verify_secret(payload.password, identity.password_hash or DUMMY_HASH)
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
                if (row.company_name, row.owner_name, row.phone_number) != (
                    payload.company_name,
                    payload.owner_name,
                    payload.phone,
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
            else:
                if await db.scalar(
                    select(Identity.id).where(Identity.phone_number == payload.phone)
                ):
                    raise DomainError(
                        "ACCOUNT_EXISTS",
                        "Registration is unavailable. Sign in or contact support.",
                        409,
                    )
                identity = Identity(
                    email=payload.email,
                    phone_number=payload.phone,
                    password_hash=hash_secret(payload.password),
                    phone_verified=False,
                    email_verified=False,
                    status=IdentityStatus.PENDING,
                )
                db.add(identity)
                await db.flush()
                row = CompanyRegistration(
                    company_name=payload.company_name,
                    owner_name=payload.owner_name,
                    email=payload.email,
                    phone_number=payload.phone,
                    identity_id=identity.id,
                    organization_id=uuid4(),
                    state="VERIFIED",
                    expires_at=datetime.now(UTC) + timedelta(days=1),
                )
                db.add(row)
                await db.flush()
    except IntegrityError:
        raise DomainError(
            "ACCOUNT_EXISTS", "Registration is unavailable. Sign in or contact support.", 409
        ) from None
    # The durable intent above survives downstream failure, retaining the same IDs.
    async with db.begin():
        row = await db.scalar(
            select(CompanyRegistration)
            .where(CompanyRegistration.identity_id == identity.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row.state == "COMPLETED":
            raise DomainError(
                "ACCOUNT_EXISTS", "Registration already completed. Please sign in.", 409
            )
        try:
            await provision_registration(db, row, request.state.correlation_id, client_ip(request))
            result = await issue(db, identity, payload, row.organization_id, row.member_id, request)
            row.state, row.last_error = "COMPLETED", None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning is temporarily unavailable.", 503
            )
    if failure:
        raise failure
    return result
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/invitations/password

### Purpose

Invitation Password

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `email` | YES | `{"type": "string", "maxLength": 320}` |
| `password` | YES | `{"type": "string", "maxLength": 128, "minLength": 1}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |
| `token` | YES | `{"type": "string", "maxLength": 128, "minLength": 32, "pattern": "^[A-Za-z0-9_-]+$"}` |

```json
{
  "properties": {
    "email": {
      "type": "string",
      "maxLength": 320,
      "title": "Email"
    },
    "password": {
      "type": "string",
      "maxLength": 128,
      "minLength": 1,
      "title": "Password"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    },
    "token": {
      "type": "string",
      "maxLength": 128,
      "minLength": 32,
      "pattern": "^[A-Za-z0-9_-]+$",
      "title": "Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "email",
    "password",
    "device",
    "token"
  ],
  "title": "InvitationPassword"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/invitations/password`

```json
{
  "email": "{{replace_with_valid_value}}",
  "password": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  },
  "token": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\password.py:257](../../../services\identity-service\app\api\v1\password.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/invitations/password", response_model=TokenResponse)
async def invitation_password(
    payload: InvitationPassword, request: Request, db: AsyncSession = Depends(get_session)
):
    from app.api.v1.invitations import organization
    from app.api.v1.registration import provision

    enabled()
    await limits(request, payload.email, "register")
    digest = hashlib.sha256(payload.token.encode()).hexdigest()
    failure = None
    try:
        async with db.begin():
            await db.execute(
                text("SELECT pg_advisory_xact_lock(hashtext(:key))"),
                {"key": "email:" + payload.email},
            )
            row = await db.scalar(
                select(InvitationOnboarding)
                .where(InvitationOnboarding.token_hash == digest)
                .with_for_update()
            )
            identity = await db.scalar(
                select(Identity)
                .where(func.lower(func.trim(Identity.email)) == payload.email)
                .with_for_update()
            )
            if row:
                if (
                    row.challenge_id is not None
                    or row.state != "VERIFIED"
                    or row.expires_at <= datetime.now(UTC)
                    or identity is None
                    or row.identity_id != identity.id
                ):
                    raise DomainError(
                        "INVITATION_INVALID",
                        "Invitation cannot be accepted. Sign in or contact your administrator.",
                        409,
                    )
            else:
                data = await organization(
                    "validate", {"token": payload.token}, request.state.correlation_id
                )
                if not data.get("email") or canonical_email(data["email"]) != payload.email:
                    raise DomainError("INVITATION_INVALID", "Invitation cannot be accepted.", 403)
                if identity is None:
                    if not 12 <= len(payload.password) <= 128:
                        raise DomainError(
                            "PASSWORD_POLICY", "Use a password between 12 and 128 characters.", 422
                        )
                    # A supplied phone is not proof: retain it in invitation metadata, never
                    # merge another phone identity or mark it verified.
                    identity = Identity(
                        email=payload.email,
                        password_hash=hash_secret(payload.password),
                        status=IdentityStatus.PENDING,
                        phone_verified=False,
                        email_verified=False,
                    )
                    db.add(identity)
                    await db.flush()
                row = InvitationOnboarding(
                    invitation_id=UUID(data["invitation_id"]),
                    token_hash=digest,
                    phone_number=data.get("phone") or "",
                    recipient_name=data["recipient_name"],
                    organization_id=UUID(data["organization_id"]),
                    identity_id=identity.id,
                    state="VERIFIED",
                    expires_at=datetime.fromisoformat(data["expires_at"]),
                )
                db.add(row)
            valid = verify_secret(payload.password, identity.password_hash or DUMMY_HASH)
            if (
                not valid
                or not identity.password_hash
                or identity.status not in {IdentityStatus.ACTIVE, IdentityStatus.PENDING}
            ):
                raise DomainError("INVALID_CREDENTIALS", "Invalid email or password.", 401)
    except IntegrityError:
        raise DomainError("INVITATION_INVALID", "Invitation cannot be accepted.", 409) from None
    async with db.begin():
        row = await db.scalar(
            select(InvitationOnboarding)
            .where(InvitationOnboarding.token_hash == digest)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        if row.state != "VERIFIED":
            raise DomainError(
                "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
            )
        try:
            await provision(
                "user",
                "/internal/v1/users/company-owner",
                {"identity_id": str(identity.id), "display_name": row.recipient_name},
                request.state.correlation_id,
            )
            result = await organization(
                "accept-email",
                {
                    "invitation_id": str(row.invitation_id),
                    "token_hash": digest,
                    "email": payload.email,
                    "identity_id": str(identity.id),
                },
                request.state.correlation_id,
            )
            if UUID(result["organization_id"]) != row.organization_id:
                raise DomainError(
                    "PROVISIONING_RETRY", "Onboarding is temporarily unavailable.", 503
                )
            row.member_id = UUID(result["member_id"])
            if identity.status == IdentityStatus.PENDING:
                await audit_and_event(
                    db,
                    action="IDENTITY_CREATED",
                    event_type="identity.created.v1",
                    aggregate_type="identity",
                    aggregate_id=identity.id,
                    identity_id=identity.id,
                    correlation_id=request.state.correlation_id,
                    ip_address=client_ip(request),
                )
            identity.status = IdentityStatus.ACTIVE
            tokens = await issue(db, identity, payload, row.organization_id, row.member_id, request)
            row.state, row.last_error = "COMPLETED", None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning is temporarily unavailable.", 503
            )
    if failure:
        raise failure
    return tokens
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/registration/company/start

### Purpose

Start

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `company_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 2}` |
| `owner_name` | YES | `{"type": "string", "maxLength": 200, "minLength": 2}` |
| `email` | YES | `{"type": "string", "maxLength": 254}` |
| `phone` | YES | `{"type": "string", "maxLength": 64}` |

```json
{
  "properties": {
    "company_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 2,
      "title": "Company Name"
    },
    "owner_name": {
      "type": "string",
      "maxLength": 200,
      "minLength": 2,
      "title": "Owner Name"
    },
    "email": {
      "type": "string",
      "maxLength": 254,
      "title": "Email"
    },
    "phone": {
      "type": "string",
      "maxLength": 64,
      "title": "Phone"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "company_name",
    "owner_name",
    "email",
    "phone"
  ],
  "title": "RegistrationStart"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/registration/company/start`

```json
{
  "company_name": "{{replace_with_valid_value}}",
  "owner_name": "{{replace_with_valid_value}}",
  "email": "{{replace_with_valid_value}}",
  "phone": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "202": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RegistrationChallenge"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\registration.py:102](../../../services\identity-service\app\api\v1\registration.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/start", response_model=RegistrationChallenge, status_code=202)
async def start(
    payload: RegistrationStart, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"registration:start:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        # Stable contact lock serializes simultaneous start submissions before any row exists.
        key = int.from_bytes(hashlib.sha256(payload.phone.encode()).digest()[:8], "big") % (
            2**63 - 1
        )
        await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
        existing = await db.scalar(
            select(Identity.id).where(
                or_(
                    Identity.phone_number == payload.phone,
                    func.lower(Identity.email) == payload.email,
                )
            )
        )
        if existing:
            raise DomainError(
                "ACCOUNT_EXISTS", "An account already exists. Sign in or contact support.", 409
            )
        # Same contact/name submission resumes the pending record, never creates another saga.
        pending = await db.scalar(
            select(CompanyRegistration)
            .where(
                CompanyRegistration.phone_number == payload.phone,
                CompanyRegistration.expires_at > datetime.now(UTC),
                CompanyRegistration.state == "PENDING",
            )
            .with_for_update()
        )
        if pending:
            raise DomainError(
                "REGISTRATION_PENDING",
                "Registration already started. Continue verification or wait for expiry.",
                409,
            )
        challenge, code = await otp_service(request).request(
            db, payload.phone, "REGISTER", client_ip(request), request.state.correlation_id
        )
        row = CompanyRegistration(
            company_name=payload.company_name,
            owner_name=payload.owner_name,
            email=payload.email,
            phone_number=payload.phone,
            challenge_id=challenge.id,
            organization_id=uuid4(),
            expires_at=challenge.expires_at,
        )
        db.add(row)
        await db.flush()
        return RegistrationChallenge(
            registration_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/registration/company/resend

### Purpose

Resend

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `registration_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "properties": {
    "registration_id": {
      "type": "string",
      "format": "uuid",
      "title": "Registration Id"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "registration_id"
  ],
  "title": "RegistrationResend"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/registration/company/resend`

```json
{
  "registration_id": "{{replace_with_actual_uuid}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "202": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RegistrationChallenge"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\registration.py:165](../../../services\identity-service\app\api\v1\registration.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/resend", response_model=RegistrationChallenge, status_code=202)
async def resend(
    payload: RegistrationResend, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"registration:resend:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        row = await registration(db, payload.registration_id)
        if row.state != "PENDING":
            raise DomainError(
                "REGISTRATION_VERIFIED",
                "Resume provisioning instead of requesting another code.",
                409,
            )
        challenge, code = await otp_service(request).request(
            db, row.phone_number, "REGISTER", client_ip(request), request.state.correlation_id
        )
        row.challenge_id, row.expires_at = challenge.id, challenge.expires_at
        return RegistrationChallenge(
            registration_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/registration/company/verify

### Purpose

Verify

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `registration_id` | YES | `{"type": "string", "format": "uuid"}` |
| `otp` | YES | `{"type": "string", "pattern": "^\\d{6}$"}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |

```json
{
  "properties": {
    "registration_id": {
      "type": "string",
      "format": "uuid",
      "title": "Registration Id"
    },
    "otp": {
      "type": "string",
      "pattern": "^\\d{6}$",
      "title": "Otp"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "registration_id",
    "otp",
    "device"
  ],
  "title": "RegistrationVerify"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/registration/company/verify`

```json
{
  "registration_id": "{{replace_with_actual_uuid}}",
  "otp": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  }
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\registration.py:224](../../../services\identity-service\app\api\v1\registration.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/verify", response_model=TokenResponse)
async def verify(
    payload: RegistrationVerify, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    limiter = RateLimiter(request.app.state.redis)
    await limiter.hit(f"registration:verify:{client_ip(request)}", 30, 3600)
    # Commit OTP failures as well, preserving attempt counters and locks.
    failure = None
    try:
        async with db.begin():
            row = await registration(db, payload.registration_id)
            if row.state == "PENDING":
                try:
                    await otp_service(request).verify(
                        db, row.challenge_id, payload.otp, client_ip(request), correlation_id
                    )
                except DomainError as exc:
                    failure = exc
                if failure is None:
                    identity = Identity(
                        phone_number=row.phone_number,
                        email=row.email,
                        phone_verified=True,
                        email_verified=False,
                        status=IdentityStatus.PENDING,
                    )
                    db.add(identity)
                    await (
                        db.flush()
                    )  # Database uniqueness serializes different challenges for one contact.
                    row.identity_id = identity.id
                    row.state = "VERIFIED"
                    row.verified_code_hash = hash_secret(payload.otp)
                    row.expires_at = datetime.now(UTC) + timedelta(minutes=30)
            else:
                if row.resume_attempts >= get_settings().otp_max_attempts:
                    failure = DomainError(
                        "OTP_TOO_MANY_ATTEMPTS", "The verification challenge is locked.", 429
                    )
                elif not verify_secret(payload.otp, row.verified_code_hash or ""):
                    row.resume_attempts += 1
                    failure = DomainError("OTP_INVALID", "The verification code is invalid.", 400)
    except IntegrityError:
        raise DomainError(
            "ACCOUNT_EXISTS", "An account already exists. Sign in or contact support.", 409
        ) from None
    if failure:
        raise failure
    # Cross-service calls are idempotent. Durable VERIFIED intent survives failures/crashes.
    async with db.begin():
        row = await registration(db, payload.registration_id)
        try:
            await provision_registration(db, row, correlation_id, client_ip(request))
        except DomainError as exc:
            row.last_error = exc.code
            failure = exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY", "Provisioning temporarily unavailable.", 503
            )
        if failure is None:
            identity = await db.get(Identity, row.identity_id)
            sessions = SessionService()
            device = await sessions.device(db, identity.id, payload.device)
            result = await sessions.create(
                db,
                identity=identity,
                device=device,
                organization_id=row.organization_id,
                member_id=row.member_id,
                ip=client_ip(request),
                user_agent=user_agent,
                correlation_id=correlation_id,
            )
            row.state, row.last_error, row.verified_code_hash = "COMPLETED", None, None
    if failure:
        raise failure
    return result
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/invitations/validate

### Purpose

Validate

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `token` | YES | `{"type": "string", "maxLength": 128, "minLength": 32, "pattern": "^[A-Za-z0-9_-]+$"}` |

```json
{
  "properties": {
    "token": {
      "type": "string",
      "maxLength": 128,
      "minLength": 32,
      "pattern": "^[A-Za-z0-9_-]+$",
      "title": "Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "token"
  ],
  "title": "InvitationToken"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/invitations/validate`

```json
{
  "token": "{{replace_with_valid_value}}"
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
        "schema": {
          "$ref": "#/components/schemas/InvitationView"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\invitations.py:152](../../../services\identity-service\app\api\v1\invitations.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/validate", response_model=InvitationView)
async def validate(
    payload: InvitationToken, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:validate:{client_ip(request)}", 60, 3600
    )
    async with db.begin():
        data = await resolve(db, payload.token, request.state.correlation_id)
    phone = data["phone"]
    return InvitationView(
        company_name=data["company_name"],
        recipient_name=data["recipient_name"],
        recipient_phone_masked=phone[:3] + "•" * max(0, len(phone) - 7) + phone[-4:],
        expires_at=data["expires_at"],
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/invitations/resend

### Purpose

Request Otp

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `token` | YES | `{"type": "string", "maxLength": 128, "minLength": 32, "pattern": "^[A-Za-z0-9_-]+$"}` |

```json
{
  "properties": {
    "token": {
      "type": "string",
      "maxLength": 128,
      "minLength": 32,
      "pattern": "^[A-Za-z0-9_-]+$",
      "title": "Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "token"
  ],
  "title": "InvitationToken"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/invitations/resend`

```json
{
  "token": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "202": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/InvitationChallenge"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\invitations.py:170](../../../services\identity-service\app\api\v1\invitations.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/request", response_model=InvitationChallenge, status_code=202)
@router.post("/resend", response_model=InvitationChallenge, status_code=202)
async def request_otp(
    payload: InvitationToken, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:request:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        data = await resolve(db, payload.token, request.state.correlation_id)
        invitation_id = UUID(data["invitation_id"])
        token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": invitation_id.int % (2**63 - 1)}
        )
        row = await db.scalar(
            select(InvitationOnboarding)
            .where(InvitationOnboarding.invitation_id == invitation_id)
            .with_for_update()
        )
        if row and row.state == "COMPLETED":
            raise DomainError(
                "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
            )
        if (
            row
            and row.state == "VERIFIED"
            and row.token_hash == token_hash
            and row.expires_at > datetime.now(UTC)
        ):
            return InvitationChallenge(
                onboarding_id=row.id, expires_at=row.expires_at, resend_after=0, verified=True
            )
        challenge, code = await otp_service(request).request(
            db, data["phone"], "INVITATION", client_ip(request), request.state.correlation_id
        )
        if row is None:
            row = InvitationOnboarding(
                invitation_id=invitation_id,
                organization_id=UUID(data["organization_id"]),
                phone_number=data["phone"],
                recipient_name=data["recipient_name"],
            )
            db.add(row)
        row.token_hash, row.challenge_id, row.expires_at = (
            token_hash,
            challenge.id,
            challenge.expires_at,
        )
        row.state, row.verified_code_hash, row.resume_attempts = "PENDING", None, 0
        await db.flush()
        return InvitationChallenge(
            onboarding_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/invitations/request

### Purpose

Request Otp

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `token` | YES | `{"type": "string", "maxLength": 128, "minLength": 32, "pattern": "^[A-Za-z0-9_-]+$"}` |

```json
{
  "properties": {
    "token": {
      "type": "string",
      "maxLength": 128,
      "minLength": 32,
      "pattern": "^[A-Za-z0-9_-]+$",
      "title": "Token"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "token"
  ],
  "title": "InvitationToken"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/invitations/request`

```json
{
  "token": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "202": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/InvitationChallenge"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\invitations.py:170](../../../services\identity-service\app\api\v1\invitations.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/request", response_model=InvitationChallenge, status_code=202)
@router.post("/resend", response_model=InvitationChallenge, status_code=202)
async def request_otp(
    payload: InvitationToken, request: Request, db: AsyncSession = Depends(get_session)
):
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:request:{client_ip(request)}", 10, 3600
    )
    async with db.begin():
        data = await resolve(db, payload.token, request.state.correlation_id)
        invitation_id = UUID(data["invitation_id"])
        token_hash = hashlib.sha256(payload.token.encode()).hexdigest()
        await db.execute(
            text("SELECT pg_advisory_xact_lock(:key)"), {"key": invitation_id.int % (2**63 - 1)}
        )
        row = await db.scalar(
            select(InvitationOnboarding)
            .where(InvitationOnboarding.invitation_id == invitation_id)
            .with_for_update()
        )
        if row and row.state == "COMPLETED":
            raise DomainError(
                "INVITATION_ACCEPTED", "Invitation already accepted. Please sign in.", 409
            )
        if (
            row
            and row.state == "VERIFIED"
            and row.token_hash == token_hash
            and row.expires_at > datetime.now(UTC)
        ):
            return InvitationChallenge(
                onboarding_id=row.id, expires_at=row.expires_at, resend_after=0, verified=True
            )
        challenge, code = await otp_service(request).request(
            db, data["phone"], "INVITATION", client_ip(request), request.state.correlation_id
        )
        if row is None:
            row = InvitationOnboarding(
                invitation_id=invitation_id,
                organization_id=UUID(data["organization_id"]),
                phone_number=data["phone"],
                recipient_name=data["recipient_name"],
            )
            db.add(row)
        row.token_hash, row.challenge_id, row.expires_at = (
            token_hash,
            challenge.id,
            challenge.expires_at,
        )
        row.state, row.verified_code_hash, row.resume_attempts = "PENDING", None, 0
        await db.flush()
        return InvitationChallenge(
            onboarding_id=row.id,
            expires_at=row.expires_at,
            resend_after=get_settings().otp_resend_cooldown_seconds,
            development_code=code,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/invitations/verify

### Purpose

Verify

### Authentication

Required: NO. Token: No bearer; challenge/refresh proof where required. Role/permission: No fixed application role. IDs do not grant cross-tenant/resource access.

### Headers

```http
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `onboarding_id` | YES | `{"type": "string", "format": "uuid"}` |
| `otp` | YES | `{"type": "string", "pattern": "^\\d{6}$"}` |
| `device` | YES | `{"additionalProperties": false, "type": "object", "required": ["installation_id", "platform", "device_name"]}` |

```json
{
  "properties": {
    "onboarding_id": {
      "type": "string",
      "format": "uuid",
      "title": "Onboarding Id"
    },
    "otp": {
      "type": "string",
      "pattern": "^\\d{6}$",
      "title": "Otp"
    },
    "device": {
      "$ref": "#/components/schemas/DeviceInput"
    }
  },
  "additionalProperties": false,
  "type": "object",
  "required": [
    "onboarding_id",
    "otp",
    "device"
  ],
  "title": "InvitationVerify"
}
```

### Postman Request

`POST http://localhost:8008/api/v1/auth/invitations/verify`

```json
{
  "onboarding_id": "{{replace_with_actual_uuid}}",
  "otp": "{{replace_with_valid_value}}",
  "device": {
    "installation_id": "{{replace_with_valid_value}}",
    "platform": "ANDROID",
    "device_name": "{{replace_with_valid_value}}",
    "device_model": "{{replace_with_valid_value}}",
    "os_version": "{{replace_with_valid_value}}",
    "app_version": "{{replace_with_valid_value}}"
  }
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
        "schema": {
          "$ref": "#/components/schemas/TokenResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\invitations.py:229](../../../services\identity-service\app\api\v1\invitations.py). Dependencies: app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/verify", response_model=TokenResponse)
async def verify(
    payload: InvitationVerify, request: Request, db: AsyncSession = Depends(get_session)
):
    correlation_id, user_agent = context(request)
    await RateLimiter(request.app.state.redis).hit(
        f"invitation:verify:{client_ip(request)}", 30, 3600
    )
    failure = None
    async with db.begin():
        row = await intent(db, payload.onboarding_id)
        if row.state == "PENDING":
            # Binding is stored server-side. No caller-controlled phone/tenant/role fields exist.
            challenge = await db.get(OTPChallenge, row.challenge_id)
            if (
                not challenge
                or challenge.phone_number != row.phone_number
                or challenge.purpose != "INVITATION"
            ):
                raise DomainError("INVITATION_INVALID", "Verification binding is invalid.", 400)
            try:
                await otp_service(request).verify(
                    db, row.challenge_id, payload.otp, client_ip(request), correlation_id
                )
            except DomainError as exc:
                failure = exc
            if failure is None:
                key = int.from_bytes(
                    hashlib.sha256(row.phone_number.encode()).digest()[:8], "big"
                ) % (2**63 - 1)
                await db.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
                identity = await db.scalar(
                    select(Identity)
                    .where(Identity.phone_number == row.phone_number)
                    .with_for_update()
                )
                reserved_invitation = identity and await db.scalar(
                    select(InvitationOnboarding.id).where(
                        InvitationOnboarding.identity_id == identity.id,
                        InvitationOnboarding.state == "VERIFIED",
                    )
                )
                if (
                    identity
                    and identity.status != IdentityStatus.ACTIVE
                    and not (
                        identity.status == IdentityStatus.PENDING
                        and (reserved_invitation or row.identity_id == identity.id)
                    )
                ):
                    failure = DomainError(
                        "ACCOUNT_UNAVAILABLE", "Contact your administrator about this account.", 403
                    )
                else:
                    if identity is None:
                        identity = Identity(
                            phone_number=row.phone_number,
                            phone_verified=True,
                            status=IdentityStatus.PENDING,
                        )
                        db.add(identity)
                        await db.flush()
                    identity.phone_verified = True
                    row.identity_id, row.state = identity.id, "VERIFIED"
                    row.verified_code_hash = hash_secret(payload.otp)
                    row.expires_at = datetime.now(UTC) + timedelta(minutes=30)
        elif row.resume_attempts >= get_settings().otp_max_attempts:
            failure = DomainError("OTP_TOO_MANY_ATTEMPTS", "Verification is locked.", 429)
        elif not verify_secret(payload.otp, row.verified_code_hash or ""):
            row.resume_attempts += 1
            failure = DomainError("OTP_INVALID", "The verification code is invalid.", 400)
    if failure:
        raise failure
    async with db.begin():
        row = await intent(db, payload.onboarding_id)
        try:
            profile = await provision(
                "user",
                "/internal/v1/users/provision",
                {"identity_id": str(row.identity_id), "display_name": row.recipient_name},
                correlation_id,
            )
            UUID(profile["user_id"])
            result = await organization(
                "accept",
                {
                    "invitation_id": str(row.invitation_id),
                    "token_hash": row.token_hash,
                    "phone": row.phone_number,
                    "identity_id": str(row.identity_id),
                },
                correlation_id,
            )
            if UUID(result["organization_id"]) != row.organization_id:
                raise ValueError()
            row.member_id = UUID(result["member_id"])
            identity = await db.scalar(
                select(Identity)
                .where(Identity.id == row.identity_id)
                .with_for_update()
                .execution_options(populate_existing=True)
            )
            if identity.status == IdentityStatus.PENDING:
                identity.status = IdentityStatus.ACTIVE
                await audit_and_event(
                    db,
                    action="IDENTITY_CREATED",
                    event_type="identity.created.v1",
                    aggregate_type="identity",
                    aggregate_id=identity.id,
                    identity_id=identity.id,
                    correlation_id=correlation_id,
                    ip_address=client_ip(request),
                )
            elif identity.status != IdentityStatus.ACTIVE:
                raise DomainError("ACCOUNT_UNAVAILABLE", "This account is unavailable.", 403)
            sessions = SessionService()
            device = await sessions.device(db, identity.id, payload.device)
            tokens = await sessions.create(
                db,
                identity=identity,
                device=device,
                organization_id=row.organization_id,
                member_id=row.member_id,
                ip=client_ip(request),
                user_agent=user_agent,
                correlation_id=correlation_id,
            )
            row.state, row.verified_code_hash, row.last_error = "COMPLETED", None, None
        except DomainError as exc:
            row.last_error, failure = exc.code, exc
        except (ValueError, KeyError, TypeError):
            row.last_error = "PROVISIONING_CONTRACT"
            failure = DomainError(
                "PROVISIONING_RETRY",
                "Onboarding is temporarily unavailable. Retry with the same code.",
                503,
            )
    if failure:
        raise failure
    return tokens
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/devices

### Purpose

Devices

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

`GET http://localhost:8008/api/v1/devices`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "items": {
            "$ref": "#/components/schemas/DeviceResponse"
          },
          "type": "array",
          "title": "Response Devices Api V1 Devices Get"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\devices.py:19](../../../services\identity-service\app\api\v1\devices.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("", response_model=list[DeviceResponse])
async def devices(
    principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_session)
):
    rows = (
        (
            await db.execute(
                select(Device)
                .where(Device.identity_id == principal.identity_id)
                .order_by(Device.last_seen_at.desc())
            )
        )
        .scalars()
        .all()
    )
    return [
        DeviceResponse(
            id=row.id,
            platform=row.platform,
            device_name=row.device_name,
            device_model=row.device_model,
            status=row.status,
            first_seen_at=row.first_seen_at,
            last_seen_at=row.last_seen_at,
            is_current=row.id == principal.device.id,
        )
        for row in rows
    ]
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/devices/{device_id}

### Purpose

Device

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
    "name": "device_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Device Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/devices/{device_id}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/DeviceResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\devices.py:49](../../../services\identity-service\app\api\v1\devices.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("/{device_id}", response_model=DeviceResponse)
async def device(
    device_id: UUID,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    row = (
        await db.execute(
            select(Device).where(
                Device.id == device_id, Device.identity_id == principal.identity_id
            )
        )
    ).scalar_one_or_none()
    if row is None:
        raise DomainError("DEVICE_NOT_FOUND", "Device was not found.", 404)
    return DeviceResponse(
        id=row.id,
        platform=row.platform,
        device_name=row.device_name,
        device_model=row.device_model,
        status=row.status,
        first_seen_at=row.first_seen_at,
        last_seen_at=row.last_seen_at,
        is_current=row.id == principal.device.id,
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/devices/{device_id}/revoke

### Purpose

Revoking the current device is defined as logout of that device/session family.

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
    "name": "device_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Device Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/devices/{device_id}/revoke`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\devices.py:76](../../../services\identity-service\app\api\v1\devices.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{device_id}/revoke", response_model=RevokeResponse)
async def revoke_device(
    device_id: UUID,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    """Revoking the current device is defined as logout of that device/session family."""
    async with command_transaction(db):
        device = (
            await db.execute(
                select(Device)
                .where(Device.id == device_id, Device.identity_id == principal.identity_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if device is None:
            raise DomainError("DEVICE_NOT_FOUND", "Device was not found.", 404)
        now = datetime.now(UTC)
        device.status, device.revoked_at = DeviceStatus.REVOKED, now
        sessions = (
            (
                await db.execute(
                    select(Session)
                    .where(Session.device_id == device.id, Session.status == SessionStatus.ACTIVE)
                    .with_for_update()
                )
            )
            .scalars()
            .all()
        )
        service = SessionService()
        for row in sessions:
            await service.revoke_session(
                db,
                row,
                request.state.correlation_id,
                request.client.host if request.client else "unknown",
                "DEVICE_REVOKED",
            )
        await audit_and_event(
            db,
            action="DEVICE_REVOKED",
            event_type="device.revoked.v1",
            aggregate_type="device",
            aggregate_id=device.id,
            correlation_id=request.state.correlation_id,
            identity_id=principal.identity_id,
            device_id=device.id,
        )
    return RevokeResponse(status="REVOKED")
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/auth/sessions

### Purpose

Sessions

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

`GET http://localhost:8008/api/v1/auth/sessions`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "items": {
            "$ref": "#/components/schemas/SessionResponse"
          },
          "type": "array",
          "title": "Response Sessions Api V1 Auth Sessions Get"
        }
      }
    }
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\sessions.py:17](../../../services\identity-service\app\api\v1\sessions.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.get("", response_model=list[SessionResponse])
async def sessions(
    principal: Principal = Depends(current_principal), db: AsyncSession = Depends(get_session)
):
    rows = (
        await db.execute(
            select(Session, Device)
            .join(Device, Device.id == Session.device_id)
            .where(Session.identity_id == principal.identity_id)
            .order_by(Session.last_activity_at.desc())
        )
    ).all()
    return [
        SessionResponse(
            id=session.id,
            device_id=device.id,
            platform=device.platform,
            device_name=device.device_name,
            status=session.status,
            created_at=session.created_at,
            last_activity_at=session.last_activity_at,
            expires_at=session.expires_at,
            ip_address=session.ip_address,
            is_current=session.id == principal.session.id,
        )
        for session, device in rows
    ]
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/auth/sessions/{session_id}/revoke

### Purpose

Revoke

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
    "name": "session_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Session Id"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/auth/sessions/{session_id}/revoke`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
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

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `IDENTITY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\identity-service\app\api\v1\sessions.py:46](../../../services\identity-service\app\api\v1\sessions.py). Dependencies: app.security.dependencies.current_principal, fastapi.security.http.<fastapi.security.http.HTTPBearer object at 0x0000015B091CFBF0>, app.db.session.get_async_session, app.db.session.get_async_session.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
@router.post("/{session_id}/revoke", response_model=RevokeResponse)
async def revoke(
    session_id: UUID,
    request: Request,
    principal: Principal = Depends(current_principal),
    db: AsyncSession = Depends(get_session),
):
    async with command_transaction(db):
        session = (
            await db.execute(
                select(Session)
                .where(Session.id == session_id, Session.identity_id == principal.identity_id)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if session is None:
            raise DomainError("SESSION_NOT_FOUND", "Session was not found.", 404)
        await SessionService().revoke_session(
            db,
            session,
            request.state.correlation_id,
            request.client.host if request.client else "unknown",
        )
    return RevokeResponse(status="REVOKED")
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: `ACCESS_TOKEN_INVALID`, `ACCOUNT_EXISTS`, `ACCOUNT_UNAVAILABLE`, `DEVICE_NOT_FOUND`, `DEVICE_REVOKED`, `EMAIL_PASSWORD_DISABLED`, `IDENTITY_INACTIVE`, `INVALID_CREDENTIALS`, `INVITATION_ACCEPTED`, `INVITATION_INVALID`, `MEMBERSHIP_INACTIVE`, `MEMBERSHIP_UNAVAILABLE`, `NOT_AUTHENTICATED`, `ORGANIZATION_SERVICE_UNAVAILABLE`, `OTP_COOLDOWN`, `OTP_DELIVERY_FAILED`, `OTP_EXPIRED`, `OTP_INVALID`, `OTP_REPLAYED`, `OTP_RESEND_COOLDOWN`, `OTP_TOO_MANY_ATTEMPTS`, `PASSWORD_POLICY`, `PHONE_INVALID`, `PHONE_OTP_DISABLED`, `PROVISIONING_RETRY`, `QR_CHALLENGE_ALREADY_USED`, `QR_CHALLENGE_EXPIRED`, `QR_CHALLENGE_INVALID`, `QR_CHALLENGE_NOT_AUTHORIZED`, `QR_CHALLENGE_NOT_FOUND`, `RATE_LIMITED`, `REFRESH_TOKEN_INVALID`, `REFRESH_TOKEN_REUSED`, `REGISTRATION_COMPLETED`, `REGISTRATION_EXPIRED`, `REGISTRATION_INVALID`, `REGISTRATION_NOT_ALLOWED`, `REGISTRATION_PENDING`, `REGISTRATION_VERIFIED`, `SESSION_EXPIRED`, `SESSION_NOT_FOUND`, `SESSION_REVOKED`, `protocol failed`.

Literal event types in implementation/tests: `auth.login_failed.v1`, `auth.login_succeeded.v1`, `auth.otp_requested.v1`, `auth.otp_verified.v1`, `auth.qr_authorized.v1`, `auth.qr_challenge_created.v1`, `auth.qr_replay_rejected.v1`, `device.linked.v1`, `device.registered.v1`, `device.revoked.v1`, `identity.created.v1`, `member.activated.v1`, `member.removed.v1`, `member.role_changed.v1`, `member.suspended.v1`, `organization.suspended.v1`, `security.refresh_reuse_detected.v1`, `session.created.v1`, `session.revoked.v1`.

Configuration field names (values omitted): `ACCESS_TOKEN_ALG`, `ACCESS_TOKEN_PRIVATE_KEY`, `ACCESS_TOKEN_PUBLIC_KEY`, `ACCESS_TOKEN_TTL`, `APP_ENV`, `AUTH_EMAIL_PASSWORD_ENABLED`, `AUTH_PHONE_OTP_ENABLED`, `CORS_ALLOWED_ORIGINS`, `DATABASE_URL`, `ORGANIZATION_SERVICE_URL`, `OTP_MAX_ATTEMPTS`, `OTP_PROVIDER`, `OTP_RESEND_COOLDOWN`, `OTP_TTL`, `QR_CHALLENGE_TTL`, `QR_DEEP_LINK_BASE`, `RABBITMQ_URL`, `RATE_LIMIT_OTP_REQUEST`, `RATE_LIMIT_OTP_VERIFY`, `RATE_LIMIT_QR_AUTHORIZE`, `RATE_LIMIT_QR_CREATE`, `REDIS_URL`, `REFRESH_TOKEN_TTL`, `REGISTRATION_POLICY`, `SERVICE_AUTH_TOKEN`, `SERVICE_NAME`, `SMS_API_BASE_URL`, `SMS_API_KEY`, `SMS_MESSAGE_TEMPLATE`, `SMS_PROVIDER`, `SMS_ROUTE`, `SMS_SENDER_ID`, `SMS_TEMPLATE_ID`, `SMS_TIMEOUT_SECONDS`, `SMS_USERNAME`, `TRUSTED_PROXIES`, `USER_SERVICE_URL`, `VONAGE_API_KEY`, `VONAGE_API_SECRET`, `VONAGE_BRAND`, `VONAGE_TIMEOUT_SECONDS`, `VONAGE_VERIFY_BASE_URL`.

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\identity-service\alembic\versions\0001_initial.py](../../../services/identity-service/alembic/versions/0001_initial.py)
- [services\identity-service\alembic\versions\0002_vonage_verify_request_mapping.py](../../../services/identity-service/alembic/versions/0002_vonage_verify_request_mapping.py)
- [services\identity-service\alembic\versions\0003_company_registration.py](../../../services/identity-service/alembic/versions/0003_company_registration.py)
- [services\identity-service\alembic\versions\0004_invitation_onboarding.py](../../../services/identity-service/alembic/versions/0004_invitation_onboarding.py)
- [services\identity-service\alembic\versions\0005_email_password.py](../../../services/identity-service/alembic/versions/0005_email_password.py)
- [services\identity-service\app\api\v1\auth.py](../../../services/identity-service/app/api/v1/auth.py)
- [services\identity-service\app\consumer_runner.py](../../../services/identity-service/app/consumer_runner.py)
- [services\identity-service\app\core\config.py](../../../services/identity-service/app/core/config.py)
- [services\identity-service\app\events\consumer_transport.py](../../../services/identity-service/app/events/consumer_transport.py)
- [services\identity-service\app\events\consumers.py](../../../services/identity-service/app/events/consumers.py)
- [services\identity-service\app\events\run_worker.py](../../../services/identity-service/app/events/run_worker.py)
- [services\identity-service\app\events\worker.py](../../../services/identity-service/app/events/worker.py)
- [services\identity-service\app\models\models.py](../../../services/identity-service/app/models/models.py)
- [services\identity-service\app\schemas\api.py](../../../services/identity-service/app/schemas/api.py)
- [services\identity-service\tests\conftest.py](../../../services/identity-service/tests/conftest.py)
- [services\identity-service\tests\contracts\test_identity_event_contracts.py](../../../services/identity-service/tests/contracts/test_identity_event_contracts.py)
- [services\identity-service\tests\integration\test_company_registration.py](../../../services/identity-service/tests/integration/test_company_registration.py)
- [services\identity-service\tests\integration\test_email_password.py](../../../services/identity-service/tests/integration/test_email_password.py)
- [services\identity-service\tests\integration\test_invitation_onboarding.py](../../../services/identity-service/tests/integration/test_invitation_onboarding.py)
- [services\identity-service\tests\security\test_identity_security.py](../../../services/identity-service/tests/security/test_identity_security.py)
- [services\identity-service\tests\unit\test_command_transaction.py](../../../services/identity-service/tests/unit/test_command_transaction.py)
- [services\identity-service\tests\unit\test_cors_config.py](../../../services/identity-service/tests/unit/test_cors_config.py)
- [services\identity-service\tests\unit\test_event_consumers.py](../../../services/identity-service/tests/unit/test_event_consumers.py)
- [services\identity-service\tests\unit\test_otp.py](../../../services/identity-service/tests/unit/test_otp.py)
- [services\identity-service\tests\unit\test_outbox_publisher.py](../../../services/identity-service/tests/unit/test_outbox_publisher.py)
- [services\identity-service\tests\unit\test_production_otp_provider.py](../../../services/identity-service/tests/unit/test_production_otp_provider.py)
- [services\identity-service\tests\unit\test_qr_login.py](../../../services/identity-service/tests/unit/test_qr_login.py)
- [services\identity-service\tests\unit\test_rabbitmq_consumer.py](../../../services/identity-service/tests/unit/test_rabbitmq_consumer.py)
- [services\identity-service\tests\unit\test_rate_limit_retry.py](../../../services/identity-service/tests/unit/test_rate_limit_retry.py)
- [services\identity-service\tests\unit\test_refresh_rotation.py](../../../services/identity-service/tests/unit/test_refresh_rotation.py)
- [services\identity-service\tests\unit\test_registration_logging.py](../../../services/identity-service/tests/unit/test_registration_logging.py)
- [services\identity-service\tests\unit\test_sessions.py](../../../services/identity-service/tests/unit/test_sessions.py)

## Active authentication policy

PRIMARY NOW: Email + Password. PRESERVED FOR FUTURE: Phone + OTP. Local AUTH_EMAIL_PASSWORD_ENABLED=true, AUTH_PHONE_OTP_ENABLED=false. POST /api/v1/auth/login, POST /api/v1/auth/registration/company and POST /api/v1/auth/invitations/password use existing session tokens; all are forwarded to Identity. No OTP/SMS occurs. Disabled OTP provider use returns PHONE_OTP_DISABLED. [Policy, constraints, limits and compatibility](../onboarding/EMAIL-PASSWORD-AUTH.md).
# Platform administration relevance

`GET /api/v1/platform/me`, `/platform/identities`, `/platform/sessions`, and `/platform/audit` require an active persistent Identity platform grant. Safe fields are explicitly selected metadata only. Password hashes, OTPs, refresh credentials, JWT keys and provider credentials are excluded. Consumer: future Admin C2 via Next bridge and Gateway.


## Personal account registration (Phase 1)

`POST /api/v1/auth/registration/personal` is public, rate-limited and requires display_name, email, E.164 phone, password and device. Success is 201 TokenResponse with null organization_id/member_id. The signed JWT omits org/mid; session/device ownership is still checked. No company is created. Phone association is unverified. Duplicate accounts return generic 409; provisioning outage returns 503 and can be resumed. See [personal accounts](../PERSONAL-ACCOUNTS.md). Existing login/refresh/me/devices/sessions/recovery/verification routes support personal accounts; workspace context still requires membership.
