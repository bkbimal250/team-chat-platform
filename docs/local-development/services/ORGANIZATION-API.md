# Organization Service API

Verified from source imports and handlers on 2026-10-05 (Asia/Calcutta). Examples are schema templates; mutations were not automatically executed.

## Service Information

| Item | Value |
|---|---|
| Service | organization |
| Framework | Django + Django REST Framework |
| Local Port | 8000 |
| Base URL | http://127.0.0.1:8000 |
| Public REST entry | http://localhost:8008 |
| OpenAPI URL | http://127.0.0.1:8000/api/schema/ |
| Health URL | http://127.0.0.1:8000/health/ready |
| PostgreSQL database | teamchat_organization_db |
| Redis | Runner endpoint 127.0.0.1:6380/0; actual dependencies in source below |
| RabbitMQ | Runner endpoint 127.0.0.1:5672, vhost `/`; actual workers below |

## Authentication

Health routes are public. Product routes use Identity-issued RS256 tokens and actual service-specific authorization. Internal routes require a service token and are operator-only. Public challenge routes require their documented challenge/OTP/refresh proof. Tenant context is derived from verified tokens; there is no invented X-Organization-ID requirement. Organization permission codes are checked against current tenant role assignments, not merely a frontend role label. See [permission defaults](../../../services/organization-service/common/authorization.py).

## Required Headers

JSON requests: `Content-Type: application/json`. Bearer routes: `Authorization: Bearer {{access_token}}`. Internal routes: `X-Internal-Service-Token: {{internal_service_token}}`. Additional parameters below are from actual schemas. Never attach credentials to signed storage URLs.

## Route Summary

| # | Method | Route | Auth | Role / permission | Purpose |
|---|---|---|---|---|---|
| 1 | GET | `/api/v1/audit-logs/` | Bearer access token | `audit.view` | list |
| 2 | GET | `/api/v1/audit-logs/{id}/` | Bearer access token | `audit.view` | retrieve |
| 3 | GET | `/api/v1/branches/` | Bearer access token | `branch.view` | list |
| 4 | POST | `/api/v1/branches/` | Bearer access token | `branch.create` | create |
| 5 | GET | `/api/v1/branches/{id}/` | Bearer access token | `branch.view` | retrieve |
| 6 | PATCH | `/api/v1/branches/{id}/` | Bearer access token | `branch.update` | partial update |
| 7 | POST | `/api/v1/branches/{id}/lifecycle/` | Bearer access token | `branch.update` | lifecycle |
| 8 | GET | `/api/v1/branches/{id}/members/` | Bearer access token | `branch.view` | members |
| 9 | POST | `/api/v1/branches/{id}/members/` | Bearer access token | `branch.update` | members |
| 10 | POST | `/api/v1/branches/{id}/members/{membership_id}/leave/` | Bearer access token | `branch.update` | remove member |
| 11 | POST | `/api/v1/branches/{id}/members/{membership_id}/primary/` | Bearer access token | `branch.update` | primary |
| 12 | GET | `/api/v1/invitations/` | Bearer access token | `invitation.view` | list |
| 13 | POST | `/api/v1/invitations/` | Bearer access token | `invitation.create` | create |
| 14 | GET | `/api/v1/invitations/{id}/` | Bearer access token | `invitation.view` | retrieve |
| 15 | POST | `/api/v1/invitations/{id}/accept/` | Bearer access token | `invitation.accept` | accept |
| 16 | POST | `/api/v1/invitations/{id}/resend/` | Bearer access token | `invitation.create` | resend |
| 17 | POST | `/api/v1/invitations/{id}/revoke/` | Bearer access token | `invitation.revoke` | revoke |
| 18 | GET | `/api/v1/members/` | Bearer access token | `member.view` | list |
| 19 | POST | `/api/v1/members/` | Bearer access token | `member.create` | create |
| 20 | GET | `/api/v1/members/{id}/` | Bearer access token | `member.view` | retrieve |
| 21 | PATCH | `/api/v1/members/{id}/` | Bearer access token | `member.update` | partial update |
| 22 | POST | `/api/v1/members/{id}/lifecycle/` | Bearer access token | `member.update` | lifecycle |
| 23 | POST | `/api/v1/members/{id}/roles/` | Bearer access token | `role.manage` | roles |
| 24 | GET | `/api/v1/organizations/current/` | Bearer access token | `organization.view` | current |
| 25 | PATCH | `/api/v1/organizations/current/` | Bearer access token | `organization.update` | current |
| 26 | POST | `/api/v1/organizations/current/lifecycle/` | Bearer access token | `organization.update` | lifecycle |
| 27 | GET | `/api/v1/organizations/current/settings/` | Bearer access token | `organization.view` | organization settings |
| 28 | PATCH | `/api/v1/organizations/current/settings/` | Bearer access token | `organization.update` | organization settings |
| 29 | GET | `/api/v1/permissions/` | Bearer access token | `role.view` | list |
| 30 | GET | `/api/v1/role-assignments/` | Bearer access token | `role.view` | list |
| 31 | GET | `/api/v1/roles/` | Bearer access token | `role.view` | list |
| 32 | POST | `/api/v1/roles/` | Bearer access token | `role.manage` | create |
| 33 | GET | `/api/v1/roles/{id}/` | Bearer access token | `role.view` | retrieve |
| 34 | GET | `/api/v1/teams/` | Bearer access token | `team.view` | list |
| 35 | POST | `/api/v1/teams/` | Bearer access token | `team.create` | create |
| 36 | GET | `/api/v1/teams/{id}/` | Bearer access token | `team.view` | retrieve |
| 37 | PATCH | `/api/v1/teams/{id}/` | Bearer access token | `team.update` | partial update |
| 38 | POST | `/api/v1/teams/{id}/lifecycle/` | Bearer access token | `team.update` | lifecycle |
| 39 | GET | `/api/v1/teams/{id}/members/` | Bearer access token | `team.view` | members |
| 40 | POST | `/api/v1/teams/{id}/members/` | Bearer access token | `team.update` | members |
| 41 | POST | `/api/v1/teams/{id}/members/{membership_id}/leave/` | Bearer access token | `team.update` | remove member |
| 42 | GET | `/health/live` | None at this layer | `No fixed application role` | live |
| 43 | GET | `/health/ready` | None at this layer | `No fixed application role` | ready |
| 44 | POST | `/api/internal/v1/company-registration/` | Internal service token | `Service caller only` | company registration |
| 45 | GET | `/api/internal/v1/identity-memberships/{identity_id}/` | Internal service token | `Service caller only` | identity memberships |
| 46 | POST | `/api/internal/v1/invitations/validate/` | Internal service token | `Service caller only` | invitation onboarding |
| 47 | POST | `/api/internal/v1/invitations/accept/` | Internal service token | `Service caller only` | invitation onboarding |
| 48 | POST | `/api/internal/v1/invitations/accept-email/` | Internal service token | `Service caller only` | invitation onboarding |
| 49 | POST | `/api/internal/v1/invitations/resume/` | Internal service token | `Service caller only` | invitation onboarding |

## GET /api/v1/audit-logs/

### Purpose


Required permission: `audit.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: audit.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "query",
    "name": "action",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "resource_type",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/audit-logs/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedAuditList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/audit-logs/{id}/

### Purpose


Required permission: `audit.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: audit.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this audit log.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/audit-logs/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Audit"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/branches/

### Purpose


Required permission: `branch.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "query",
    "name": "city",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "status",
    "schema": {
      "type": "string",
      "enum": [
        "ACTIVE",
        "DELETED",
        "DISABLED"
      ]
    },
    "description": "* `ACTIVE` - Active\n* `DISABLED` - Disabled\n* `DELETED` - Deleted"
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/branches/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedBranchList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/branches/

### Purpose


Required permission: `branch.create`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.create. IDs do not grant cross-tenant/resource access.

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
| `name` | YES | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `code` | YES | `{"type": "string", "minLength": 1, "maxLength": 50}` |
| `email` | NO | `{"type": "string", "format": "email", "nullable": true, "maxLength": 254}` |
| `phone` | NO | `{"type": "string", "nullable": true, "maxLength": 32}` |
| `address` | NO | `{"type": "string", "nullable": true}` |
| `city` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `state` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `country` | YES | `{"type": "string", "minLength": 1, "maxLength": 2}` |
| `postal_code` | NO | `{"type": "string", "nullable": true, "maxLength": 20}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50
    },
    "email": {
      "type": "string",
      "format": "email",
      "nullable": true,
      "maxLength": 254
    },
    "phone": {
      "type": "string",
      "nullable": true,
      "maxLength": 32
    },
    "address": {
      "type": "string",
      "nullable": true
    },
    "city": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "state": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "country": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2
    },
    "postal_code": {
      "type": "string",
      "nullable": true,
      "maxLength": 20
    }
  },
  "required": [
    "code",
    "country",
    "name"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/branches/`

```json
{
  "name": "{{replace_with_valid_value}}",
  "code": "{{replace_with_valid_value}}",
  "email": "{{replace_with_valid_value}}",
  "phone": "{{replace_with_valid_value}}",
  "address": "{{replace_with_valid_value}}",
  "city": "{{replace_with_valid_value}}",
  "state": "{{replace_with_valid_value}}",
  "country": "{{replace_with_valid_value}}",
  "postal_code": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Branch"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:36](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = create_resource(
            self.context, self.model, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/branches/{id}/

### Purpose


Required permission: `branch.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/branches/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Branch"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/branches/{id}/

### Purpose


Required permission: `branch.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `name` | NO | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `code` | NO | `{"type": "string", "minLength": 1, "maxLength": 50}` |
| `email` | NO | `{"type": "string", "format": "email", "nullable": true, "maxLength": 254}` |
| `phone` | NO | `{"type": "string", "nullable": true, "maxLength": 32}` |
| `address` | NO | `{"type": "string", "nullable": true}` |
| `city` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `state` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `country` | NO | `{"type": "string", "minLength": 1, "maxLength": 2}` |
| `postal_code` | NO | `{"type": "string", "nullable": true, "maxLength": 20}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 50
    },
    "email": {
      "type": "string",
      "format": "email",
      "nullable": true,
      "maxLength": 254
    },
    "phone": {
      "type": "string",
      "nullable": true,
      "maxLength": 32
    },
    "address": {
      "type": "string",
      "nullable": true
    },
    "city": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "state": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "country": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2
    },
    "postal_code": {
      "type": "string",
      "nullable": true,
      "maxLength": 20
    }
  }
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/branches/{id}/`

```json
{
  "name": "{{replace_with_valid_value}}",
  "code": "{{replace_with_valid_value}}",
  "email": "{{replace_with_valid_value}}",
  "phone": "{{replace_with_valid_value}}",
  "address": "{{replace_with_valid_value}}",
  "city": "{{replace_with_valid_value}}",
  "state": "{{replace_with_valid_value}}",
  "country": "{{replace_with_valid_value}}",
  "postal_code": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Branch"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:44](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def partial_update(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = update_resource(
            self.context, self.model, instance.id, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/branches/{id}/lifecycle/

### Purpose


Required permission: `branch.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `status` | YES | `{"type": "string", "minLength": 1, "maxLength": 20}` |

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20
    }
  },
  "required": [
    "status"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/branches/{id}/lifecycle/`

```json
{
  "status": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Branch"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:53](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=LifecycleInput)
    @action(detail=True, methods=["post"])
    def lifecycle(self, request, pk=None):
        instance = self.get_object()
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = transition(
            self.context,
            self.model,
            instance.id,
            serializer.validated_data["status"],
            self.aggregate,
        )
        return Response(self.get_serializer(result).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/branches/{id}/members/

### Purpose


Required permission: `branch.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/branches/{id}/members/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/BranchMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\branches\api.py:24](../../../services\organization-service\apps\branches\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=BranchMembershipInput, responses=BranchMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        return super().members(request, pk)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/branches/{id}/members/

### Purpose


Required permission: `branch.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `member_id` | YES | `{"type": "string", "format": "uuid"}` |
| `is_primary` | NO | `{"type": "boolean", "default": false}` |

```json
{
  "type": "object",
  "properties": {
    "member_id": {
      "type": "string",
      "format": "uuid"
    },
    "is_primary": {
      "type": "boolean",
      "default": false
    }
  },
  "required": [
    "member_id"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/branches/{id}/members/`

```json
{
  "member_id": "{{replace_with_actual_uuid}}",
  "is_primary": false
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/BranchMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\branches\api.py:24](../../../services\organization-service\apps\branches\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=BranchMembershipInput, responses=BranchMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        return super().members(request, pk)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/branches/{id}/members/{membership_id}/leave/

### Purpose


Required permission: `branch.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  },
  {
    "in": "path",
    "name": "membership_id",
    "schema": {
      "type": "string",
      "pattern": "^[0-9a-f-]{36}$"
    },
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/branches/{id}/members/{membership_id}/leave/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/BranchMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\branches\api.py:29](../../../services\organization-service\apps\branches\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=None, responses=BranchMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/leave"
    )
    def remove_member(self, request, pk=None, membership_id=None):
        return super().remove_member(request, pk, membership_id)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/branches/{id}/members/{membership_id}/primary/

### Purpose


Required permission: `branch.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: branch.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this branch.",
    "required": true
  },
  {
    "in": "path",
    "name": "membership_id",
    "schema": {
      "type": "string",
      "pattern": "^[0-9a-f-]{36}$"
    },
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/branches/{id}/members/{membership_id}/primary/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/BranchMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\branches\api.py:36](../../../services\organization-service\apps\branches\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=None, responses=BranchMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/primary"
    )
    def primary(self, request, pk=None, membership_id=None):
        parent = self.get_object()
        membership = tenant_get(BranchMembership, self.context, membership_id)
        if membership.branch_id != parent.id:
            from django.http import Http404

            raise Http404
        result = set_primary_branch(self.context, membership.id)
        return Response(BranchMembershipSerializer(result).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/invitations/

### Purpose


Required permission: `invitation.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/invitations/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedInvitationList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/invitations/

### Purpose


Required permission: `invitation.create`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.create. IDs do not grant cross-tenant/resource access.

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
| `team_id` | NO | `{"type": "string", "format": "uuid", "nullable": true}` |
| `branch_id` | NO | `{"type": "string", "format": "uuid", "nullable": true}` |
| `intended_role_id` | YES | `{"type": "string", "format": "uuid"}` |
| `expires_at` | NO | `{"type": "string", "format": "date-time"}` |
| `recipient_name` | NO | `{"type": "string", "maxLength": 200}` |
| `recipient_phone` | NO | `{"type": "string", "maxLength": 32}` |
| `recipient_email` | NO | `{"type": "string", "format": "email", "maxLength": 254}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "team_id": {
      "type": "string",
      "format": "uuid",
      "nullable": true
    },
    "branch_id": {
      "type": "string",
      "format": "uuid",
      "nullable": true
    },
    "intended_role_id": {
      "type": "string",
      "format": "uuid"
    },
    "expires_at": {
      "type": "string",
      "format": "date-time"
    },
    "recipient_name": {
      "type": "string",
      "maxLength": 200
    },
    "recipient_phone": {
      "type": "string",
      "maxLength": 32
    },
    "recipient_email": {
      "type": "string",
      "format": "email",
      "maxLength": 254
    }
  },
  "required": [
    "intended_role_id"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/invitations/`

```json
{
  "team_id": "{{replace_with_actual_uuid}}",
  "branch_id": "{{replace_with_actual_uuid}}",
  "intended_role_id": "{{replace_with_actual_uuid}}",
  "expires_at": "{{replace_with_valid_timestamp}}",
  "recipient_name": "{{replace_with_valid_value}}",
  "recipient_phone": "{{replace_with_valid_value}}",
  "recipient_email": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Invitation"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\invitations\api.py:43](../../../services\organization-service\apps\invitations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = create_invitation(self.context, serializer.validated_data)
        result = self.get_serializer(invitation).data
        if getattr(invitation, "development_url", None):
            result["development_url"] = invitation.development_url
        return Response(result, status=201)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/invitations/{id}/

### Purpose


Required permission: `invitation.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this invitation.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/invitations/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Invitation"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/invitations/{id}/accept/

### Purpose


Required permission: `invitation.accept`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.accept. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this invitation.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `member_id` | YES | `{"type": "string", "format": "uuid"}` |

```json
{
  "type": "object",
  "properties": {
    "member_id": {
      "type": "string",
      "format": "uuid"
    }
  },
  "required": [
    "member_id"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/invitations/{id}/accept/`

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
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Invitation"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\invitations\api.py:58](../../../services\organization-service\apps\invitations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=AcceptInvitationInput)
    @action(detail=True, methods=["post"])
    def accept(self, request, pk=None):
        serializer = AcceptInvitationInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = accept_invitation(
            self.context, self.get_object().id, **serializer.validated_data
        )
        return Response(self.get_serializer(invitation).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/invitations/{id}/resend/

### Purpose


Required permission: `invitation.create`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.create. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this invitation.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/invitations/{id}/resend/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Invitation"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\invitations\api.py:68](../../../services\organization-service\apps\invitations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        invitation = resend_invitation(self.context, self.get_object().id)
        return Response(
            {**self.get_serializer(invitation).data, "development_url": invitation.development_url}
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/invitations/{id}/revoke/

### Purpose


Required permission: `invitation.revoke`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: invitation.revoke. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this invitation.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/invitations/{id}/revoke/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Invitation"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\invitations\api.py:52](../../../services\organization-service\apps\invitations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        invitation = revoke_invitation(self.context, self.get_object().id)
        return Response(self.get_serializer(invitation).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/members/

### Purpose


Required permission: `member.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: member.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "query",
    "name": "branch",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  },
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "role",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "status",
    "schema": {
      "type": "string",
      "enum": [
        "ACTIVE",
        "INVITED",
        "LEFT",
        "REMOVED",
        "SUSPENDED"
      ]
    },
    "description": "* `INVITED` - Invited\n* `ACTIVE` - Active\n* `SUSPENDED` - Suspended\n* `LEFT` - Left\n* `REMOVED` - Removed"
  },
  {
    "in": "query",
    "name": "team",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/members/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedMemberList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/members/

### Purpose


Required permission: `member.create`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: member.create. IDs do not grant cross-tenant/resource access.

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
| `display_name` | YES | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `employee_code` | NO | `{"type": "string", "nullable": true, "maxLength": 50}` |
| `designation` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `department` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "display_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "employee_code": {
      "type": "string",
      "nullable": true,
      "maxLength": 50
    },
    "designation": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "department": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    }
  },
  "required": [
    "display_name"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/members/`

```json
{
  "display_name": "{{replace_with_valid_value}}",
  "employee_code": "{{replace_with_valid_value}}",
  "designation": "{{replace_with_valid_value}}",
  "department": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Member"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:36](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = create_resource(
            self.context, self.model, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/members/{id}/

### Purpose


Required permission: `member.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: member.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this member.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/members/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Member"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/members/{id}/

### Purpose


Required permission: `member.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: member.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this member.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `display_name` | NO | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `employee_code` | NO | `{"type": "string", "nullable": true, "maxLength": 50}` |
| `designation` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |
| `department` | NO | `{"type": "string", "nullable": true, "maxLength": 100}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "display_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "employee_code": {
      "type": "string",
      "nullable": true,
      "maxLength": 50
    },
    "designation": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    },
    "department": {
      "type": "string",
      "nullable": true,
      "maxLength": 100
    }
  }
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/members/{id}/`

```json
{
  "display_name": "{{replace_with_valid_value}}",
  "employee_code": "{{replace_with_valid_value}}",
  "designation": "{{replace_with_valid_value}}",
  "department": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Member"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:44](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def partial_update(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = update_resource(
            self.context, self.model, instance.id, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/members/{id}/lifecycle/

### Purpose


Required permission: `member.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: member.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this member.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `status` | YES | `{"type": "string", "minLength": 1, "maxLength": 20}` |

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20
    }
  },
  "required": [
    "status"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/members/{id}/lifecycle/`

```json
{
  "status": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Member"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:53](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=LifecycleInput)
    @action(detail=True, methods=["post"])
    def lifecycle(self, request, pk=None):
        instance = self.get_object()
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = transition(
            self.context,
            self.model,
            instance.id,
            serializer.validated_data["status"],
            self.aggregate,
        )
        return Response(self.get_serializer(result).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/members/{id}/roles/

### Purpose


Required permission: `role.manage`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.manage. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this member.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `role_id` | YES | `{"type": "string", "format": "uuid"}` |
| `remove` | NO | `{"type": "boolean", "default": false}` |

```json
{
  "type": "object",
  "properties": {
    "role_id": {
      "type": "string",
      "format": "uuid"
    },
    "remove": {
      "type": "boolean",
      "default": false
    }
  },
  "required": [
    "role_id"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/members/{id}/roles/`

```json
{
  "role_id": "{{replace_with_actual_uuid}}",
  "remove": false
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Member"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\members\api.py:32](../../../services\organization-service\apps\members\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=RoleAssignmentInput, responses=MemberSerializer)
    @action(detail=True, methods=["post"])
    def roles(self, request, pk=None):
        member = self.get_object()
        serializer = RoleAssignmentInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        member = assign_role(self.context, member.id, **serializer.validated_data)
        return Response(self.get_serializer(member).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/organizations/current/

### Purpose


Required permission: `organization.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: organization.view. IDs do not grant cross-tenant/resource access.

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

`GET http://localhost:8008/api/v1/organizations/current/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Organization"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\organizations\api.py:27](../../../services\organization-service\apps\organizations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @action(detail=False, methods=["get", "patch"])
    def current(self, request):
        organization = Organization.objects.get(id=self.context.organization_id)
        if request.method == "PATCH":
            serializer = self.get_serializer(organization, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            organization = update_organization(self.context, serializer.validated_data)
        return Response(self.get_serializer(organization).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/organizations/current/

### Purpose


Required permission: `organization.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: organization.update. IDs do not grant cross-tenant/resource access.

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
| `name` | NO | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `slug` | NO | `{"type": "string", "minLength": 1, "maxLength": 100, "pattern": "^[-a-zA-Z0-9_]+$"}` |
| `display_name` | NO | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `organization_type` | NO | `{"enum": ["BUSINESS", "NONPROFIT", "OTHER"], "type": "string"}` |
| `logo_media_id` | NO | `{"type": "string", "format": "uuid", "nullable": true}` |
| `email` | NO | `{"type": "string", "format": "email", "nullable": true, "maxLength": 254}` |
| `phone` | NO | `{"type": "string", "nullable": true, "maxLength": 32}` |
| `timezone` | NO | `{"type": "string", "minLength": 1, "maxLength": 64}` |
| `country_code` | NO | `{"type": "string", "minLength": 1, "maxLength": 2}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "slug": {
      "type": "string",
      "minLength": 1,
      "maxLength": 100,
      "pattern": "^[-a-zA-Z0-9_]+$"
    },
    "display_name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "organization_type": {
      "$ref": "#/components/schemas/OrganizationTypeEnum"
    },
    "logo_media_id": {
      "type": "string",
      "format": "uuid",
      "nullable": true
    },
    "email": {
      "type": "string",
      "format": "email",
      "nullable": true,
      "maxLength": 254
    },
    "phone": {
      "type": "string",
      "nullable": true,
      "maxLength": 32
    },
    "timezone": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64
    },
    "country_code": {
      "type": "string",
      "minLength": 1,
      "maxLength": 2
    }
  }
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/organizations/current/`

```json
{
  "name": "{{replace_with_valid_value}}",
  "slug": "{{replace_with_valid_value}}",
  "display_name": "{{replace_with_valid_value}}",
  "organization_type": "BUSINESS",
  "logo_media_id": "{{replace_with_actual_uuid}}",
  "email": "{{replace_with_valid_value}}",
  "phone": "{{replace_with_valid_value}}",
  "timezone": "{{replace_with_valid_value}}",
  "country_code": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Organization"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\organizations\api.py:27](../../../services\organization-service\apps\organizations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @action(detail=False, methods=["get", "patch"])
    def current(self, request):
        organization = Organization.objects.get(id=self.context.organization_id)
        if request.method == "PATCH":
            serializer = self.get_serializer(organization, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            organization = update_organization(self.context, serializer.validated_data)
        return Response(self.get_serializer(organization).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/organizations/current/lifecycle/

### Purpose


Required permission: `organization.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: organization.update. IDs do not grant cross-tenant/resource access.

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
| `status` | YES | `{"type": "string", "minLength": 1, "maxLength": 20}` |

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20
    }
  },
  "required": [
    "status"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/organizations/current/lifecycle/`

```json
{
  "status": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Organization"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\organizations\api.py:46](../../../services\organization-service\apps\organizations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=LifecycleInput)
    @action(detail=False, methods=["post"], url_path="current/lifecycle")
    def lifecycle(self, request):
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = set_organization_status(self.context, serializer.validated_data["status"])
        return Response(self.get_serializer(organization).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/organizations/current/settings/

### Purpose


Required permission: `organization.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: organization.view. IDs do not grant cross-tenant/resource access.

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

`GET http://localhost:8008/api/v1/organizations/current/settings/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Settings"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\organizations\api.py:36](../../../services\organization-service\apps\organizations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=SettingsSerializer, responses=SettingsSerializer)
    @action(detail=False, methods=["get", "patch"], url_path="current/settings")
    def organization_settings(self, request):
        settings = Organization.objects.get(id=self.context.organization_id).settings
        if request.method == "PATCH":
            serializer = SettingsSerializer(settings, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            settings = update_settings(self.context, serializer.validated_data)
        return Response(SettingsSerializer(settings).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/organizations/current/settings/

### Purpose


Required permission: `organization.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: organization.update. IDs do not grant cross-tenant/resource access.

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
| `allow_member_invites` | NO | `{"type": "boolean"}` |
| `allow_group_creation` | NO | `{"type": "boolean"}` |
| `allow_external_chat` | NO | `{"type": "boolean"}` |
| `max_members` | NO | `{"type": "integer", "maximum": 2147483647, "minimum": 0, "nullable": true}` |
| `max_teams` | NO | `{"type": "integer", "maximum": 2147483647, "minimum": 0, "nullable": true}` |
| `default_timezone` | NO | `{"type": "string", "minLength": 1, "maxLength": 64}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "allow_member_invites": {
      "type": "boolean"
    },
    "allow_group_creation": {
      "type": "boolean"
    },
    "allow_external_chat": {
      "type": "boolean"
    },
    "max_members": {
      "type": "integer",
      "maximum": 2147483647,
      "minimum": 0,
      "nullable": true
    },
    "max_teams": {
      "type": "integer",
      "maximum": 2147483647,
      "minimum": 0,
      "nullable": true
    },
    "default_timezone": {
      "type": "string",
      "minLength": 1,
      "maxLength": 64
    }
  }
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/organizations/current/settings/`

```json
{
  "allow_member_invites": false,
  "allow_group_creation": false,
  "allow_external_chat": false,
  "max_members": 0,
  "max_teams": 0,
  "default_timezone": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Settings"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\organizations\api.py:36](../../../services\organization-service\apps\organizations\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=SettingsSerializer, responses=SettingsSerializer)
    @action(detail=False, methods=["get", "patch"], url_path="current/settings")
    def organization_settings(self, request):
        settings = Organization.objects.get(id=self.context.organization_id).settings
        if request.method == "PATCH":
            serializer = SettingsSerializer(settings, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            settings = update_settings(self.context, serializer.validated_data)
        return Response(SettingsSerializer(settings).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/permissions/

### Purpose


Required permission: `role.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/permissions/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedPermissionList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/role-assignments/

### Purpose


Required permission: `role.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "member",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "in": "query",
    "name": "role",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/role-assignments/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedRoleAssignmentList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/roles/

### Purpose


Required permission: `role.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/roles/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedRoleList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/roles/

### Purpose


Required permission: `role.manage`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.manage. IDs do not grant cross-tenant/resource access.

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
| `name` | YES | `{"type": "string", "minLength": 1, "maxLength": 80}` |
| `permission_codes` | YES | `{"type": "array", "maxItems": 100}` |

```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 80
    },
    "permission_codes": {
      "type": "array",
      "items": {
        "type": "string",
        "minLength": 1,
        "maxLength": 80
      },
      "maxItems": 100
    }
  },
  "required": [
    "name",
    "permission_codes"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/roles/`

```json
{
  "name": "{{replace_with_valid_value}}",
  "permission_codes": [
    "{{replace_with_valid_value}}"
  ]
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Role"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\roles\api.py:22](../../../services\organization-service\apps\roles\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=CustomRoleInput, responses=RoleSerializer)
    def create(self, request):
        serializer = CustomRoleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        role = create_custom_role(self.context, **serializer.validated_data)
        return Response(self.get_serializer(role).data, status=201)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/roles/{id}/

### Purpose


Required permission: `role.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: role.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this role.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/roles/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Role"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/teams/

### Purpose


Required permission: `team.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "query",
    "name": "branch",
    "schema": {
      "type": "string",
      "format": "uuid"
    }
  },
  {
    "name": "cursor",
    "required": false,
    "in": "query",
    "description": "The pagination cursor value.",
    "schema": {
      "type": "string"
    }
  },
  {
    "name": "page_size",
    "required": false,
    "in": "query",
    "description": "Number of results to return per page.",
    "schema": {
      "type": "integer"
    }
  },
  {
    "name": "search",
    "required": false,
    "in": "query",
    "description": "A search term.",
    "schema": {
      "type": "string"
    }
  },
  {
    "in": "query",
    "name": "status",
    "schema": {
      "type": "string",
      "enum": [
        "ACTIVE",
        "DELETED",
        "DISABLED"
      ]
    },
    "description": "* `ACTIVE` - Active\n* `DISABLED` - Disabled\n* `DELETED` - Deleted"
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/teams/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/PaginatedTeamList"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:37](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/teams/

### Purpose


Required permission: `team.create`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.create. IDs do not grant cross-tenant/resource access.

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
| `branch_id` | NO | `{"type": "string", "format": "uuid", "nullable": true}` |
| `name` | YES | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `description` | NO | `{"type": "string", "nullable": true}` |
| `type` | NO | `{"enum": ["STANDARD", "DEPARTMENT", "PROJECT"], "type": "string"}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "branch_id": {
      "type": "string",
      "format": "uuid",
      "nullable": true
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "description": {
      "type": "string",
      "nullable": true
    },
    "type": {
      "$ref": "#/components/schemas/TypeEnum"
    }
  },
  "required": [
    "name"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/teams/`

```json
{
  "branch_id": "{{replace_with_actual_uuid}}",
  "name": "{{replace_with_valid_value}}",
  "description": "{{replace_with_valid_value}}",
  "type": "STANDARD"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "201": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Team"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:36](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = create_resource(
            self.context, self.model, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data, status=status.HTTP_201_CREATED)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/teams/{id}/

### Purpose


Required permission: `team.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/teams/{id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Team"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py:53](../../../services\organization-service\.venv\Lib\site-packages\rest_framework\mixins.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## PATCH /api/v1/teams/{id}/

### Purpose


Required permission: `team.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `branch_id` | NO | `{"type": "string", "format": "uuid", "nullable": true}` |
| `name` | NO | `{"type": "string", "minLength": 1, "maxLength": 200}` |
| `description` | NO | `{"type": "string", "nullable": true}` |
| `type` | NO | `{"enum": ["STANDARD", "DEPARTMENT", "PROJECT"], "type": "string"}` |

```json
{
  "type": "object",
  "description": "Reject unknown/read-only input rather than silently accepting tenant/identity spoofing.",
  "properties": {
    "branch_id": {
      "type": "string",
      "format": "uuid",
      "nullable": true
    },
    "name": {
      "type": "string",
      "minLength": 1,
      "maxLength": 200
    },
    "description": {
      "type": "string",
      "nullable": true
    },
    "type": {
      "$ref": "#/components/schemas/TypeEnum"
    }
  }
}
```

### Postman Request

`PATCH http://localhost:8008/api/v1/teams/{id}/`

```json
{
  "branch_id": "{{replace_with_actual_uuid}}",
  "name": "{{replace_with_valid_value}}",
  "description": "{{replace_with_valid_value}}",
  "type": "STANDARD"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Team"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:44](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    def partial_update(self, request, pk=None):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        instance = update_resource(
            self.context, self.model, instance.id, serializer.validated_data, self.aggregate
        )
        return Response(self.get_serializer(instance).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/teams/{id}/lifecycle/

### Purpose


Required permission: `team.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `status` | YES | `{"type": "string", "minLength": 1, "maxLength": 20}` |

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "minLength": 1,
      "maxLength": 20
    }
  },
  "required": [
    "status"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/teams/{id}/lifecycle/`

```json
{
  "status": "{{replace_with_valid_value}}"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/Team"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\common\api.py:53](../../../services\organization-service\common\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=LifecycleInput)
    @action(detail=True, methods=["post"])
    def lifecycle(self, request, pk=None):
        instance = self.get_object()
        serializer = LifecycleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        result = transition(
            self.context,
            self.model,
            instance.id,
            serializer.validated_data["status"],
            self.aggregate,
        )
        return Response(self.get_serializer(result).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/v1/teams/{id}/members/

### Purpose


Required permission: `team.view`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.view. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://localhost:8008/api/v1/teams/{id}/members/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/TeamMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\teams\api.py:29](../../../services\organization-service\apps\teams\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=TeamMembershipInput, responses=TeamMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        parent = self.get_object()
        if request.method == "POST":
            serializer = self.membership_input(data=request.data)
            serializer.is_valid(raise_exception=True)
            membership = add_membership(
                self.context, parent.id, branch=self.branch_membership, **serializer.validated_data
            )
            return Response(self.membership_serializer(membership).data, status=201)
        queryset = tenant_queryset(self.membership_model, self.context).filter(
            **{self.aggregate: parent}
        )
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.membership_serializer(page, many=True).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/teams/{id}/members/

### Purpose


Required permission: `team.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
Content-Type: application/json
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  }
]
```

### Request Body

| Field | Required | Type / constraints |
|---|---|---|
| `member_id` | YES | `{"type": "string", "format": "uuid"}` |
| `role` | NO | `{"allOf": [{"$ref": "#/components/schemas/TeamMembershipInputRoleEnum"}], "default": "MEMBER"}` |

```json
{
  "type": "object",
  "properties": {
    "member_id": {
      "type": "string",
      "format": "uuid"
    },
    "role": {
      "allOf": [
        {
          "$ref": "#/components/schemas/TeamMembershipInputRoleEnum"
        }
      ],
      "default": "MEMBER"
    }
  },
  "required": [
    "member_id"
  ]
}
```

### Postman Request

`POST http://localhost:8008/api/v1/teams/{id}/members/`

```json
{
  "member_id": "{{replace_with_actual_uuid}}",
  "role": "OWNER"
}
```

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/TeamMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\teams\api.py:29](../../../services\organization-service\apps\teams\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=TeamMembershipInput, responses=TeamMembershipSerializer)
    @action(detail=True, methods=["get", "post"])
    def members(self, request, pk=None):
        parent = self.get_object()
        if request.method == "POST":
            serializer = self.membership_input(data=request.data)
            serializer.is_valid(raise_exception=True)
            membership = add_membership(
                self.context, parent.id, branch=self.branch_membership, **serializer.validated_data
            )
            return Response(self.membership_serializer(membership).data, status=201)
        queryset = tenant_queryset(self.membership_model, self.context).filter(
            **{self.aggregate: parent}
        )
        page = self.paginate_queryset(queryset)
        return self.get_paginated_response(self.membership_serializer(page, many=True).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/v1/teams/{id}/members/{membership_id}/leave/

### Purpose


Required permission: `team.update`. Tenant-scoped identifiers return 404 outside the current organization. Errors use `error.code`, `error.message`, `error.details`, `error.correlation_id`.

### Authentication

Required: YES. Token: Bearer access token. Role/permission: team.update. IDs do not grant cross-tenant/resource access.

### Headers

```http
Authorization: Bearer {{access_token}}
```

### Path, Query and Header Parameters

```json
[
  {
    "in": "path",
    "name": "id",
    "schema": {
      "type": "string",
      "format": "uuid"
    },
    "description": "A UUID string identifying this team.",
    "required": true
  },
  {
    "in": "path",
    "name": "membership_id",
    "schema": {
      "type": "string",
      "pattern": "^[0-9a-f-]{36}$"
    },
    "required": true
  }
]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://localhost:8008/api/v1/teams/{id}/members/{membership_id}/leave/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

```json
{
  "200": {
    "content": {
      "application/json": {
        "schema": {
          "$ref": "#/components/schemas/TeamMembership"
        }
      }
    },
    "description": ""
  }
}
```

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services\organization-service\apps\teams\api.py:46](../../../services\organization-service\apps\teams\api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
    @extend_schema(request=None, responses=TeamMembershipSerializer)
    @action(
        detail=True, methods=["post"], url_path=r"members/(?P<membership_id>[0-9a-f-]{36})/leave"
    )
    def remove_member(self, request, pk=None, membership_id=None):
        parent = self.get_object()
        membership = end_membership(
            self.context, parent.id, UUID(membership_id), branch=self.branch_membership
        )
        return Response(self.membership_serializer(membership).data)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

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

`GET http://127.0.0.1:8000/health/live`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/config/urls.py:34](../../../services/organization-service/config/urls.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def live(request):
    return JsonResponse({"status": "alive"})
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

`GET http://127.0.0.1:8000/health/ready`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/config/urls.py:38](../../../services/organization-service/config/urls.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception:
        return JsonResponse({"status": "not_ready"}, status=503)
    return JsonResponse(
        {
            "status": "ready",
            "database": "available",
            "broker": "asynchronous; monitored by outbox worker",
        }
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/internal/v1/company-registration/

### Purpose

company registration

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://127.0.0.1:8000/api/internal/v1/company-registration/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/organizations/internal_api.py:58](../../../services/organization-service/apps/organizations/internal_api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def company_registration(request):
    """Authenticated Identity saga only. The organization ID is its idempotency key."""
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        data = json.loads(request.body)
        if set(data) != {"organization_id", "identity_id", "company_name", "owner_name", "email"}:
            raise ValueError()
        organization_id, identity_id = UUID(data["organization_id"]), UUID(data["identity_id"])
        with transaction.atomic():
            # Serialize retries even before the organization exists.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT pg_advisory_xact_lock(%s)", [organization_id.int % (2**63 - 1)]
                )
            existing = Organization.objects.filter(id=organization_id).first()
            if existing:
                owner = Member.objects.get(organization=existing, user_id=identity_id)
            else:
                existing, owner = provision_organization(
                    name=data["company_name"],
                    slug="company-" + organization_id.hex,
                    owner_name=data["owner_name"],
                    owner_user_id=identity_id,
                    organization_id=organization_id,
                    email=data["email"],
                    correlation_id=getattr(request, "correlation_id", ""),
                )
        return JsonResponse({"organization_id": str(existing.id), "member_id": str(owner.id)})
    except (ValueError, TypeError, KeyError, Member.DoesNotExist, ValidationError, DomainError):
        return JsonResponse({"error": {"code": "PROVISIONING_CONFLICT"}}, status=409)
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## GET /api/internal/v1/identity-memberships/{identity_id}/

### Purpose

identity memberships

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`GET http://127.0.0.1:8000/api/internal/v1/identity-memberships/{identity_id}/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/organizations/internal_api.py:19](../../../services/organization-service/apps/organizations/internal_api.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def identity_memberships(request, identity_id: UUID):
    """Versioned internal contract used by identity-service only; never expose it through a gateway."""
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse(
            {
                "error": {
                    "code": "SERVICE_UNAUTHORIZED",
                    "message": "Unauthorized service identity.",
                    "details": {},
                    "correlation_id": getattr(request, "correlation_id", ""),
                }
            },
            status=401,
        )
    rows = Member.objects.filter(
        user_id=identity_id,
        status=Member.Status.ACTIVE,
        organization__status=Organization.Status.ACTIVE,
    ).values("organization_id", "id", "status")
    return JsonResponse(
        {
            "contract_version": "identity-memberships.v1",
            "memberships": [
                {
                    "organization_id": str(row["organization_id"]),
                    "member_id": str(row["id"]),
                    "status": row["status"],
                }
                for row in rows
            ],
        }
    )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/internal/v1/invitations/validate/

### Purpose

invitation onboarding

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://127.0.0.1:8000/api/internal/v1/invitations/validate/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/invitations/onboarding.py:165](../../../services/organization-service/apps/invitations/onboarding.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def invitation_onboarding(request, action):
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        body = json.loads(request.body)
        if action == "validate" and set(body) == {"token"}:
            token = body["token"]
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            invitation = (
                Invitation.objects.select_related("organization")
                .filter(token_hash=digest(token))
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            available(invitation)
            return JsonResponse(snapshot(invitation))
        if action == "resume" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            invitation = (
                Invitation.objects.select_related("organization", "accepted_member")
                .filter(
                    id=UUID(body["invitation_id"]),
                    token_hash=body["token_hash"],
                    recipient_phone=body["phone"],
                    status="ACCEPTED",
                    accepted_member__user_id=UUID(body["identity_id"]),
                    accepted_member__status="ACTIVE",
                    organization__status="ACTIVE",
                )
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            return JsonResponse(snapshot(invitation))
        if action == "accept-email" and set(body) == {
            "invitation_id",
            "token_hash",
            "email",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    None,
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                    email=body["email"],
                )
            )
        if action == "accept" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    body["phone"],
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                )
            )
        raise ValueError()
    except DomainError as exc:
        return JsonResponse(
            {"error": {"code": exc.machine_code, "message": str(exc.detail)}},
            status=exc.status_code,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": {"code": "INVITATION_INVALID", "message": "This invitation is invalid."}},
            status=400,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/internal/v1/invitations/accept/

### Purpose

invitation onboarding

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://127.0.0.1:8000/api/internal/v1/invitations/accept/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/invitations/onboarding.py:165](../../../services/organization-service/apps/invitations/onboarding.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def invitation_onboarding(request, action):
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        body = json.loads(request.body)
        if action == "validate" and set(body) == {"token"}:
            token = body["token"]
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            invitation = (
                Invitation.objects.select_related("organization")
                .filter(token_hash=digest(token))
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            available(invitation)
            return JsonResponse(snapshot(invitation))
        if action == "resume" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            invitation = (
                Invitation.objects.select_related("organization", "accepted_member")
                .filter(
                    id=UUID(body["invitation_id"]),
                    token_hash=body["token_hash"],
                    recipient_phone=body["phone"],
                    status="ACCEPTED",
                    accepted_member__user_id=UUID(body["identity_id"]),
                    accepted_member__status="ACTIVE",
                    organization__status="ACTIVE",
                )
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            return JsonResponse(snapshot(invitation))
        if action == "accept-email" and set(body) == {
            "invitation_id",
            "token_hash",
            "email",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    None,
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                    email=body["email"],
                )
            )
        if action == "accept" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    body["phone"],
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                )
            )
        raise ValueError()
    except DomainError as exc:
        return JsonResponse(
            {"error": {"code": exc.machine_code, "message": str(exc.detail)}},
            status=exc.status_code,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": {"code": "INVITATION_INVALID", "message": "This invitation is invalid."}},
            status=400,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/internal/v1/invitations/accept-email/

### Purpose

invitation onboarding

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://127.0.0.1:8000/api/internal/v1/invitations/accept-email/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/invitations/onboarding.py:165](../../../services/organization-service/apps/invitations/onboarding.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def invitation_onboarding(request, action):
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        body = json.loads(request.body)
        if action == "validate" and set(body) == {"token"}:
            token = body["token"]
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            invitation = (
                Invitation.objects.select_related("organization")
                .filter(token_hash=digest(token))
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            available(invitation)
            return JsonResponse(snapshot(invitation))
        if action == "resume" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            invitation = (
                Invitation.objects.select_related("organization", "accepted_member")
                .filter(
                    id=UUID(body["invitation_id"]),
                    token_hash=body["token_hash"],
                    recipient_phone=body["phone"],
                    status="ACCEPTED",
                    accepted_member__user_id=UUID(body["identity_id"]),
                    accepted_member__status="ACTIVE",
                    organization__status="ACTIVE",
                )
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            return JsonResponse(snapshot(invitation))
        if action == "accept-email" and set(body) == {
            "invitation_id",
            "token_hash",
            "email",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    None,
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                    email=body["email"],
                )
            )
        if action == "accept" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    body["phone"],
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                )
            )
        raise ValueError()
    except DomainError as exc:
        return JsonResponse(
            {"error": {"code": exc.machine_code, "message": str(exc.detail)}},
            status=exc.status_code,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": {"code": "INVITATION_INVALID", "message": "This invitation is invalid."}},
            status=400,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## POST /api/internal/v1/invitations/resume/

### Purpose

invitation onboarding

### Authentication

Required: YES. Token: Internal service token. Role/permission: Service caller only. IDs do not grant cross-tenant/resource access.

### Headers

```http
X-Internal-Service-Token: {{internal_service_token}}
```

### Path, Query and Header Parameters

```json
[]
```

### Request Body

No declared JSON body. Hidden/internal requests are defined by the exact handler below; do not infer a request from a response.



### Postman Request

`POST http://127.0.0.1:8000/api/internal/v1/invitations/resume/`

No generated JSON body; supply only the actual parameters/handler input.

Replace placeholders using authorized local fixture IDs. For PATCH submit only fields you intend to change. Read-only/server-owned fields are excluded from generated body templates; unsupported optional fields should be omitted. Never run all mutations automatically.

### Responses and Errors

Not declared in OpenAPI. Exact response/errors appear in the implementation below.

An empty schema means no response model was declared, not an empty response. References resolve against the adjacent `ORGANIZATION-OPENAPI.json`. Source-defined propagated error codes are listed in Service Verification below; not every error applies to every route.

### Implementation and Manual Verification

Source: [services/organization-service/apps/invitations/onboarding.py:165](../../../services/organization-service/apps/invitations/onboarding.py). Dependencies: See middleware/handler.

<details><summary>Exact handler: response fields, authorization and service calls</summary>

```python
def invitation_onboarding(request, action):
    supplied = request.headers.get("X-Internal-Service-Token", "")
    if not settings.INTERNAL_SERVICE_TOKEN or not hmac.compare_digest(
        supplied, settings.INTERNAL_SERVICE_TOKEN
    ):
        return JsonResponse({"error": {"code": "SERVICE_UNAUTHORIZED"}}, status=401)
    try:
        body = json.loads(request.body)
        if action == "validate" and set(body) == {"token"}:
            token = body["token"]
            if not isinstance(token, str) or not 32 <= len(token) <= 128:
                raise ValueError()
            invitation = (
                Invitation.objects.select_related("organization")
                .filter(token_hash=digest(token))
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            available(invitation)
            return JsonResponse(snapshot(invitation))
        if action == "resume" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            invitation = (
                Invitation.objects.select_related("organization", "accepted_member")
                .filter(
                    id=UUID(body["invitation_id"]),
                    token_hash=body["token_hash"],
                    recipient_phone=body["phone"],
                    status="ACCEPTED",
                    accepted_member__user_id=UUID(body["identity_id"]),
                    accepted_member__status="ACTIVE",
                    organization__status="ACTIVE",
                )
                .first()
            )
            if invitation is None:
                raise DomainError("INVITATION_INVALID", "This invitation is invalid.", 404)
            return JsonResponse(snapshot(invitation))
        if action == "accept-email" and set(body) == {
            "invitation_id",
            "token_hash",
            "email",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    None,
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                    email=body["email"],
                )
            )
        if action == "accept" and set(body) == {
            "invitation_id",
            "token_hash",
            "phone",
            "identity_id",
        }:
            return JsonResponse(
                accept_bound(
                    UUID(body["invitation_id"]),
                    body["token_hash"],
                    body["phone"],
                    UUID(body["identity_id"]),
                    getattr(request, "correlation_id", ""),
                )
            )
        raise ValueError()
    except DomainError as exc:
        return JsonResponse(
            {"error": {"code": exc.machine_code, "message": str(exc.detail)}},
            status=exc.status_code,
        )
    except (ValueError, TypeError, KeyError):
        return JsonResponse(
            {"error": {"code": "INVITATION_INVALID", "message": "This invitation is invalid."}},
            status=400,
        )
```

</details>

Send one request at a time. Verify actual status and response fields above. Check mutations with the corresponding authorized GET before repeating them. Keep Owner/Employee tokens separate. Internal routes are direct operator calls and never publicly forwarded. Destructive actions require disposable fixtures. OTP requests can send paid SMS when Vonage is active: no automatic retries.

## Service Verification

Domain/protocol error codes found in source: `CONSTRAINT_CONFLICT`, `DELIVERY_UNAVAILABLE`, `EMAIL_INVALID`, `IDENTITY_ALREADY_LINKED`, `IDENTITY_REQUIRED`, `INACTIVE_MEMBERSHIP_TARGET`, `INVALID_COUNTRY_CODE`, `INVALID_EXPIRY`, `INVALID_MEMBERSHIP_TARGET`, `INVALID_PERMISSION`, `INVALID_TIMEZONE`, `INVALID_TRANSITION`, `INVITATION_ACCEPTED`, `INVITATION_EXPIRED`, `INVITATION_INVALID`, `INVITATION_NOT_PENDING`, `INVITATION_PENDING`, `INVITATION_UNAVAILABLE`, `INVITES_DISABLED`, `LAST_OWNER`, `MEMBERSHIP_ENDED`, `MEMBER_ALREADY_EXISTS`, `MEMBER_INACTIVE`, `NAME_INVALID`, `OWNER_ASSIGNMENT_DENIED`, `PERMISSION_DENIED`, `PHONE_INVALID`, `PHONE_REQUIRED`, `PHONE_VERIFICATION_REQUIRED`, `RESOURCE_TERMINAL`, `ROLE_ESCALATION_DENIED`, `TENANT_INACTIVE`, `TENANT_LIMIT_REACHED`.

Literal event types in implementation/tests: `invitation.accepted.v1`, `member.activated.v2`, `member.created.v2`, `member.removed.v2`, `member.role_changed.v2`, `member.suspended.v2`, `team.created.v1`, `team_membership.created.v1`.

Configuration field names (values omitted): .

Runner defaults override container defaults. APIs run on Windows; PostgreSQL/Redis/RabbitMQ run in Docker. `dev.py start` enables email/password and disables phone OTP. Optional OTP providers remain preserved; enable explicitly only when testing that capability.

### Models, Schemas, Configuration, Authorization, Migrations, Events and Tests

- [services\organization-service\apps\audit\api.py](../../../services/organization-service/apps/audit/api.py)
- [services\organization-service\apps\audit\migrations\0001_initial.py](../../../services/organization-service/apps/audit/migrations/0001_initial.py)
- [services\organization-service\apps\audit\migrations\__init__.py](../../../services/organization-service/apps/audit/migrations/__init__.py)
- [services\organization-service\apps\audit\models.py](../../../services/organization-service/apps/audit/models.py)
- [services\organization-service\apps\branches\api.py](../../../services/organization-service/apps/branches/api.py)
- [services\organization-service\apps\branches\migrations\0001_initial.py](../../../services/organization-service/apps/branches/migrations/0001_initial.py)
- [services\organization-service\apps\branches\migrations\__init__.py](../../../services/organization-service/apps/branches/migrations/__init__.py)
- [services\organization-service\apps\branches\models.py](../../../services/organization-service/apps/branches/models.py)
- [services\organization-service\apps\invitations\api.py](../../../services/organization-service/apps/invitations/api.py)
- [services\organization-service\apps\invitations\migrations\0001_initial.py](../../../services/organization-service/apps/invitations/migrations/0001_initial.py)
- [services\organization-service\apps\invitations\migrations\0002_recipient_onboarding.py](../../../services/organization-service/apps/invitations/migrations/0002_recipient_onboarding.py)
- [services\organization-service\apps\invitations\migrations\__init__.py](../../../services/organization-service/apps/invitations/migrations/__init__.py)
- [services\organization-service\apps\invitations\models.py](../../../services/organization-service/apps/invitations/models.py)
- [services\organization-service\apps\members\api.py](../../../services/organization-service/apps/members/api.py)
- [services\organization-service\apps\members\migrations\0001_initial.py](../../../services/organization-service/apps/members/migrations/0001_initial.py)
- [services\organization-service\apps\members\migrations\__init__.py](../../../services/organization-service/apps/members/migrations/__init__.py)
- [services\organization-service\apps\members\models.py](../../../services/organization-service/apps/members/models.py)
- [services\organization-service\apps\organizations\api.py](../../../services/organization-service/apps/organizations/api.py)
- [services\organization-service\apps\organizations\internal_api.py](../../../services/organization-service/apps/organizations/internal_api.py)
- [services\organization-service\apps\organizations\migrations\0001_initial.py](../../../services/organization-service/apps/organizations/migrations/0001_initial.py)
- [services\organization-service\apps\organizations\migrations\0002_tenant_integrity.py](../../../services/organization-service/apps/organizations/migrations/0002_tenant_integrity.py)
- [services\organization-service\apps\organizations\migrations\__init__.py](../../../services/organization-service/apps/organizations/migrations/__init__.py)
- [services\organization-service\apps\organizations\models.py](../../../services/organization-service/apps/organizations/models.py)
- [services\organization-service\apps\roles\api.py](../../../services/organization-service/apps/roles/api.py)
- [services\organization-service\apps\roles\migrations\0001_initial.py](../../../services/organization-service/apps/roles/migrations/0001_initial.py)
- [services\organization-service\apps\roles\migrations\__init__.py](../../../services/organization-service/apps/roles/migrations/__init__.py)
- [services\organization-service\apps\roles\models.py](../../../services/organization-service/apps/roles/models.py)
- [services\organization-service\apps\teams\api.py](../../../services/organization-service/apps/teams/api.py)
- [services\organization-service\apps\teams\migrations\0001_initial.py](../../../services/organization-service/apps/teams/migrations/0001_initial.py)
- [services\organization-service\apps\teams\migrations\__init__.py](../../../services/organization-service/apps/teams/migrations/__init__.py)
- [services\organization-service\apps\teams\models.py](../../../services/organization-service/apps/teams/models.py)
- [services\organization-service\common\api.py](../../../services/organization-service/common/api.py)
- [services\organization-service\common\authorization.py](../../../services/organization-service/common/authorization.py)
- [services\organization-service\common\models.py](../../../services/organization-service/common/models.py)
- [services\organization-service\common\schema.py](../../../services/organization-service/common/schema.py)
- [services\organization-service\events\outbox\management\commands\publish_outbox.py](../../../services/organization-service/events/outbox/management/commands/publish_outbox.py)
- [services\organization-service\events\outbox\management\commands\retry_outbox.py](../../../services/organization-service/events/outbox/management/commands/retry_outbox.py)
- [services\organization-service\events\outbox\migrations\0001_initial.py](../../../services/organization-service/events/outbox/migrations/0001_initial.py)
- [services\organization-service\events\outbox\migrations\__init__.py](../../../services/organization-service/events/outbox/migrations/__init__.py)
- [services\organization-service\events\outbox\models.py](../../../services/organization-service/events/outbox/models.py)
- [services\organization-service\events\outbox\worker.py](../../../services/organization-service/events/outbox/worker.py)
- [services\organization-service\events\schemas\generate_schema.py](../../../services/organization-service/events/schemas/generate_schema.py)
- [services\organization-service\tests\conftest.py](../../../services/organization-service/tests/conftest.py)
- [services\organization-service\tests\integration\test_concurrency.py](../../../services/organization-service/tests/integration/test_concurrency.py)
- [services\organization-service\tests\integration\test_rabbitmq.py](../../../services/organization-service/tests/integration/test_rabbitmq.py)
- [services\organization-service\tests\security\test_tenants.py](../../../services/organization-service/tests/security/test_tenants.py)
- [services\organization-service\tests\test_api.py](../../../services/organization-service/tests/test_api.py)
- [services\organization-service\tests\test_company_registration.py](../../../services/organization-service/tests/test_company_registration.py)
- [services\organization-service\tests\test_constraints.py](../../../services/organization-service/tests/test_constraints.py)
- [services\organization-service\tests\test_domain.py](../../../services/organization-service/tests/test_domain.py)
- [services\organization-service\tests\test_employee_invitations.py](../../../services/organization-service/tests/test_employee_invitations.py)
- [services\organization-service\tests\test_outbox.py](../../../services/organization-service/tests/test_outbox.py)
- [services\organization-service\tests\test_proxy_security.py](../../../services/organization-service/tests/test_proxy_security.py)
# Platform administration relevance

`GET /api/v1/platform/organizations/` and `/{id}/` require Identity's `platform.organizations.read`; they return bounded structure metadata. Existing tenant APIs keep their ordinary tenant permissions. Invitation tokens, private chat data and secrets are excluded. Consumer: future Admin C2 via Gateway.

