# Gateway Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | gateway |
| Framework | FastAPI |
| Local Port | 8008 |
| Base URL | http://127.0.0.1:8008 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8008/openapi.json |
| Health URL | http://127.0.0.1:8008/health/ready |
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
| 3 | DELETE | `/{path:path}` | None at this layer | `No fixed application role` | proxy |
| 4 | GET | `/{path:path}` | None at this layer | `No fixed application role` | proxy |
| 5 | HEAD | `/{path:path}` | None at this layer | `No fixed application role` | proxy |
| 6 | PATCH | `/{path:path}` | None at this layer | `No fixed application role` | proxy |
| 7 | POST | `/{path:path}` | None at this layer | `No fixed application role` | proxy |
| 8 | PUT | `/{path:path}` | None at this layer | `No fixed application role` | proxy |

## GET /health/live

### Purpose

live

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

`GET http://127.0.0.1:8008/health/live`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:76](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.get("/health/live", include_in_schema=False)
    async def live() -> dict[str, str]:
        return {"status": "alive"}
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /health/ready

### Purpose

ready

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

`GET http://127.0.0.1:8008/health/ready`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:80](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.get("/health/ready", include_in_schema=False)
    async def ready(request: Request) -> JSONResponse:
        initialized = bool(getattr(request.app.state, "ready", False))
        return JSONResponse(
            {"status": "ready" if initialized else "not_ready"},
            status_code=200 if initialized else 503,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## DELETE /{path:path}

### Purpose

proxy

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

`DELETE http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /{path:path}

### Purpose

proxy

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

`GET http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## HEAD /{path:path}

### Purpose

proxy

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

`HEAD http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /{path:path}

### Purpose

proxy

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

`PATCH http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /{path:path}

### Purpose

proxy

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

`POST http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PUT /{path:path}

### Purpose

proxy

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

`PUT http://127.0.0.1:8008/{path:path}`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `GATEWAY-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\gateway-service\app\main.py:88](../../../services\gateway-service\app\main.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @app.api_route(
        "/{path:path}",
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD"],
        include_in_schema=False,
    )
    async def proxy(path: str, request: Request) -> Response:
        public_path = f"/{path}"
        owner = owner_for(public_path)
        correlation_id = _safe_correlation_id(request.headers.get("x-correlation-id"))
        if owner is None:
            return JSONResponse(
                {"detail": "Not found", "correlation_id": correlation_id}, status_code=404
            )

        length = request.headers.get("content-length")
        if length and length.isdigit() and int(length) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )
        body = await request.body()
        if len(body) > config.max_request_bytes:
            return JSONResponse(
                {"detail": "Request body too large", "correlation_id": correlation_id},
                status_code=413,
            )

        headers = {
            name: value
            for name, value in request.headers.items()
            if name.lower() in REQUEST_HEADERS
        }
        headers["x-correlation-id"] = correlation_id
        if request.client:
            headers["x-forwarded-for"] = request.client.host
        forwarded_proto = request.headers.get("x-forwarded-proto")
        headers["x-forwarded-proto"] = (
            forwarded_proto if forwarded_proto in {"http", "https"} else request.url.scheme
        )
        url = f"{config.upstreams[owner]}{public_path}"
        try:
            upstream = await request.app.state.upstreams.request(
                request.method, url, params=request.query_params, headers=headers, content=body
            )
        except httpx.TimeoutException:
            return JSONResponse(
                {"detail": "Upstream request timed out", "correlation_id": correlation_id},
                status_code=504,
            )
        except httpx.RequestError:
            return JSONResponse(
                {"detail": "Upstream service unavailable", "correlation_id": correlation_id},
                status_code=502,
            )
        response_headers = {
            name: value
            for name, value in upstream.headers.items()
            if name.lower() in RESPONSE_HEADERS
        }
        response_headers.setdefault("x-correlation-id", correlation_id)
        return Response(
            content=upstream.content,
            status_code=upstream.status_code,
            headers=response_headers,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: .

Literal event types in implementation/tests: .

Configuration field names (values omitted): `app_env`, `conversation_url`, `cors_allowed_origins`, `identity_url`, `max_request_bytes`, `media_url`, `messaging_url`, `notification_url`, `organization_url`, `upstream_connect_timeout_seconds`, `upstream_read_timeout_seconds`, `user_url`.

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\gateway-service\app\config.py](../../../services/gateway-service/app/config.py)
- [services\gateway-service\tests\test_gateway.py](../../../services/gateway-service/tests/test_gateway.py)

## Forwarding Ownership

```python
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class RouteOwner:
    name: str
    service: str
    pattern: re.Pattern[str]


# Specific messaging conversation subresources precede the conversation catch-all.
ROUTE_OWNERS = (
    RouteOwner(
        "messaging-conversation",
        "messaging",
        re.compile(r"^/api/v1/conversations/[^/]+/(?:messages(?:/.*)?|delivered|read)/?$"),
    ),
    RouteOwner("messaging-message", "messaging", re.compile(r"^/api/v1/messages(?:/.*)?$")),
    RouteOwner("identity-auth", "identity", re.compile(r"^/api/v1/auth(?:/.*)?$")),
    RouteOwner("identity-devices", "identity", re.compile(r"^/api/v1/devices(?:/.*)?$")),
    RouteOwner("user", "user", re.compile(r"^/api/v1/users(?:/.*)?$")),
    RouteOwner("conversation", "conversation", re.compile(r"^/api/v1/conversations(?:/.*)?$")),
    RouteOwner("media", "media", re.compile(r"^/api/v1/media(?:/.*)?$")),
    RouteOwner("notification", "notification", re.compile(r"^/api/v1/notifications(?:/.*)?$")),
    RouteOwner(
        "organization",
        "organization",
        re.compile(
            r"^/api/v1/(?:organizations|branches|teams|members|invitations|roles|"
            r"permissions|role-assignments|audit-logs)(?:/.*)?$"
        ),
    ),
)


def owner_for(path: str) -> str | None:
    matches = [owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(path)]
    if not matches:
        return None
    return matches[0]


def collisions_for(paths: list[str]) -> dict[str, list[str]]:
    collisions: dict[str, list[str]] = {}
    for path in paths:
        services = {owner.service for owner in ROUTE_OWNERS if owner.pattern.fullmatch(path)}
        if len(services) > 1:
            collisions[path] = sorted(services)
    return collisions

```

Gateway readiness does not prove every upstream is running. Internal routes are not forwarded.

## Active authentication policy

PRIMARY NOW: Email + Password. PRESERVED FOR FUTURE: Phone + OTP. Local AUTH_EMAIL_PASSWORD_ENABLED=true, AUTH_PHONE_OTP_ENABLED=false. POST /api/v1/auth/login, POST /api/v1/auth/registration/company and POST /api/v1/auth/invitations/password use existing session tokens; all are forwarded to Identity. No OTP/SMS occurs. Disabled OTP provider use returns PHONE_OTP_DISABLED. [Policy, constraints, limits and compatibility](../onboarding/EMAIL-PASSWORD-AUTH.md).
# Platform administration relevance

`GET /api/v1/platform/services` is Gateway's only C1 platform operation. It first validates `platform.services.read` with Identity, then returns only each service's live/ready booleans. It does not expose upstream URLs, configuration or credentials. Admin browsers use the Next bridge, never direct service URLs.



## Personal contact discovery

Authenticated `/api/v1/contacts` CRUD and `/api/v1/contacts/match` route through Gateway to User. See [contact contracts, limits and privacy](../CONTACT-DISCOVERY.md). Contacts require user ownership, not company membership.
