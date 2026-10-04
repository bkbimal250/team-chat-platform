# Organization API

Last verified: 2026-10-04. Port: 8000.

Commands: `python scripts/local/dev.py start`, `python scripts/local/dev.py health`. Expected: live/ready 200. Client routes use Gateway 8008; internal routes use the service directly. No AWS required.

Full request/response constraints and component definitions are in the adjacent OPENAPI.json. JSON below is a schema template; replace placeholders. A route inventory is not a claim that all destructive mutations were exercised.


## GET /api/schema/

Purpose: schema_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[
  {
    "in": "query",
    "name": "format",
    "schema": {
      "type": "string",
      "enum": [
        "json",
        "yaml"
      ]
    }
  },
  {
    "in": "query",
    "name": "lang",
    "schema": {
      "type": "string",
      "enum": [
        "af",
        "ar",
        "ar-dz",
        "ast",
        "az",
        "be",
        "bg",
        "bn",
        "br",
        "bs",
        "ca",
        "ckb",
        "cs",
        "cy",
        "da",
        "de",
        "dsb",
        "el",
        "en",
        "en-au",
        "en-gb",
        "eo",
        "es",
        "es-ar",
        "es-co",
        "es-mx",
        "es-ni",
        "es-ve",
        "et",
        "eu",
        "fa",
        "fi",
        "fr",
        "fy",
        "ga",
        "gd",
        "gl",
        "he",
        "hi",
        "hr",
        "hsb",
        "hu",
        "hy",
        "ia",
        "id",
        "ig",
        "io",
        "is",
        "it",
        "ja",
        "ka",
        "kab",
        "kk",
        "km",
        "kn",
        "ko",
        "ky",
        "lb",
        "lt",
        "lv",
        "mk",
        "ml",
        "mn",
        "mr",
        "ms",
        "my",
        "nb",
        "ne",
        "nl",
        "nn",
        "os",
        "pa",
        "pl",
        "pt",
        "pt-br",
        "ro",
        "ru",
        "sk",
        "sl",
        "sq",
        "sr",
        "sr-latn",
        "sv",
        "sw",
        "ta",
        "te",
        "tg",
        "th",
        "tk",
        "tr",
        "tt",
        "udm",
        "ug",
        "uk",
        "ur",
        "uz",
        "vi",
        "zh-hans",
        "zh-hant"
      ]
    }
  }
]
```

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
```json
{
  "200": {
    "content": {
      "application/vnd.oai.openapi": {
        "schema": {
          "type": "object",
          "additionalProperties": {}
        }
      },
      "application/yaml": {
        "schema": {
          "type": "object",
          "additionalProperties": {}
        }
      },
      "application/vnd.oai.openapi+json": {
        "schema": {
          "type": "object",
          "additionalProperties": {}
        }
      },
      "application/json": {
        "schema": {
          "type": "object",
          "additionalProperties": {}
        }
      }
    },
    "description": ""
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/schema/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/audit-logs/

Purpose: v1_audit_logs_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/audit-logs/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/audit-logs/{id}/

Purpose: v1_audit_logs_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/audit-logs/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/branches/

Purpose: v1_branches_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/branches/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/branches/

Purpose: v1_branches_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/BranchRequest"
}
```

Postman body template:
```json
{
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "code": "<REPLACE_WITH_VALID_VALUE>",
  "email": "<REPLACE_WITH_VALID_VALUE>",
  "phone": "<REPLACE_WITH_VALID_VALUE>",
  "address": "<REPLACE_WITH_VALID_VALUE>",
  "city": "<REPLACE_WITH_VALID_VALUE>",
  "state": "<REPLACE_WITH_VALID_VALUE>",
  "country": "<REPLACE_WITH_VALID_VALUE>",
  "postal_code": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/branches/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/branches/{id}/

Purpose: v1_branches_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/branches/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/branches/{id}/

Purpose: v1_branches_partial_update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/PatchedBranchRequest"
}
```

Postman body template:
```json
{
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "code": "<REPLACE_WITH_VALID_VALUE>",
  "email": "<REPLACE_WITH_VALID_VALUE>",
  "phone": "<REPLACE_WITH_VALID_VALUE>",
  "address": "<REPLACE_WITH_VALID_VALUE>",
  "city": "<REPLACE_WITH_VALID_VALUE>",
  "state": "<REPLACE_WITH_VALID_VALUE>",
  "country": "<REPLACE_WITH_VALID_VALUE>",
  "postal_code": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/branches/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/branches/{id}/lifecycle/

Purpose: v1_branches_lifecycle_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```

Postman body template:
```json
{
  "status": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/branches/{id}/lifecycle/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/branches/{id}/members/

Purpose: v1_branches_members_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/branches/{id}/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/branches/{id}/members/

Purpose: v1_branches_members_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/BranchMembershipInputRequest"
}
```

Postman body template:
```json
{
  "member_id": "00000000-0000-4000-8000-000000000001",
  "is_primary": false
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/branches/{id}/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/branches/{id}/members/{membership_id}/leave/

Purpose: v1_branches_members_leave_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/branches/{id}/members/{membership_id}/leave/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/branches/{id}/members/{membership_id}/primary/

Purpose: v1_branches_members_primary_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/branches/{id}/members/{membership_id}/primary/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/invitations/

Purpose: v1_invitations_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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
  },
  {
    "in": "query",
    "name": "status",
    "schema": {
      "type": "string",
      "enum": [
        "ACCEPTED",
        "EXPIRED",
        "PENDING",
        "REVOKED"
      ]
    },
    "description": "* `PENDING` - Pending\n* `ACCEPTED` - Accepted\n* `EXPIRED` - Expired\n* `REVOKED` - Revoked"
  }
]
```

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/invitations/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/invitations/

Purpose: v1_invitations_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/InvitationRequest"
}
```

Postman body template:
```json
{
  "team_id": "00000000-0000-4000-8000-000000000001",
  "branch_id": "00000000-0000-4000-8000-000000000001",
  "intended_role_id": "00000000-0000-4000-8000-000000000001",
  "expires_at": "2026-10-04T00:00:00Z"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/invitations/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/invitations/{id}/

Purpose: v1_invitations_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/invitations/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/invitations/{id}/accept/

Purpose: v1_invitations_accept_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/AcceptInvitationInputRequest"
}
```

Postman body template:
```json
{
  "member_id": "00000000-0000-4000-8000-000000000001"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/invitations/{id}/accept/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/invitations/{id}/revoke/

Purpose: v1_invitations_revoke_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/invitations/{id}/revoke/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/members/

Purpose: v1_members_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/members/

Purpose: v1_members_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/MemberRequest"
}
```

Postman body template:
```json
{
  "display_name": "<REPLACE_WITH_VALID_VALUE>",
  "employee_code": "<REPLACE_WITH_VALID_VALUE>",
  "designation": "<REPLACE_WITH_VALID_VALUE>",
  "department": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/members/{id}/

Purpose: v1_members_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/members/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/members/{id}/

Purpose: v1_members_partial_update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/PatchedMemberRequest"
}
```

Postman body template:
```json
{
  "display_name": "<REPLACE_WITH_VALID_VALUE>",
  "employee_code": "<REPLACE_WITH_VALID_VALUE>",
  "designation": "<REPLACE_WITH_VALID_VALUE>",
  "department": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/members/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/members/{id}/lifecycle/

Purpose: v1_members_lifecycle_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```

Postman body template:
```json
{
  "status": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/members/{id}/lifecycle/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/members/{id}/roles/

Purpose: v1_members_roles_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/RoleAssignmentInputRequest"
}
```

Postman body template:
```json
{
  "role_id": "00000000-0000-4000-8000-000000000001",
  "remove": false
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/members/{id}/roles/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/organizations/current/

Purpose: v1_organizations_current_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/organizations/current/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/organizations/current/

Purpose: v1_organizations_current_partial_update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/PatchedOrganizationRequest"
}
```

Postman body template:
```json
{
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "slug": "<REPLACE_WITH_VALID_VALUE>",
  "display_name": "<REPLACE_WITH_VALID_VALUE>",
  "organization_type": "BUSINESS",
  "logo_media_id": "00000000-0000-4000-8000-000000000001",
  "email": "<REPLACE_WITH_VALID_VALUE>",
  "phone": "<REPLACE_WITH_VALID_VALUE>",
  "timezone": "<REPLACE_WITH_VALID_VALUE>",
  "country_code": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/organizations/current/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/organizations/current/lifecycle/

Purpose: v1_organizations_current_lifecycle_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```

Postman body template:
```json
{
  "status": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/organizations/current/lifecycle/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/organizations/current/settings/

Purpose: v1_organizations_current_settings_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/organizations/current/settings/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/organizations/current/settings/

Purpose: v1_organizations_current_settings_partial_update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/PatchedSettingsRequest"
}
```

Postman body template:
```json
{
  "allow_member_invites": true,
  "allow_group_creation": true,
  "allow_external_chat": true,
  "max_members": 0,
  "max_teams": 0,
  "default_timezone": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/organizations/current/settings/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/permissions/

Purpose: v1_permissions_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/permissions/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/role-assignments/

Purpose: v1_role_assignments_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/role-assignments/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/roles/

Purpose: v1_roles_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/roles/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/roles/

Purpose: v1_roles_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/CustomRoleInputRequest"
}
```

Postman body template:
```json
{
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "permission_codes": [
    "<REPLACE_WITH_VALID_VALUE>"
  ]
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/roles/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/roles/{id}/

Purpose: v1_roles_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/roles/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/teams/

Purpose: v1_teams_list

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/teams/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/teams/

Purpose: v1_teams_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/TeamRequest"
}
```

Postman body template:
```json
{
  "branch_id": "00000000-0000-4000-8000-000000000001",
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "description": "<REPLACE_WITH_VALID_VALUE>",
  "type": "STANDARD"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/teams/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/teams/{id}/

Purpose: v1_teams_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/teams/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/teams/{id}/

Purpose: v1_teams_partial_update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/PatchedTeamRequest"
}
```

Postman body template:
```json
{
  "branch_id": "00000000-0000-4000-8000-000000000001",
  "name": "<REPLACE_WITH_VALID_VALUE>",
  "description": "<REPLACE_WITH_VALID_VALUE>",
  "type": "STANDARD"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/teams/{id}/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/teams/{id}/lifecycle/

Purpose: v1_teams_lifecycle_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/LifecycleInputRequest"
}
```

Postman body template:
```json
{
  "status": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/teams/{id}/lifecycle/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/teams/{id}/members/

Purpose: v1_teams_members_retrieve

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/teams/{id}/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/teams/{id}/members/

Purpose: v1_teams_members_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/TeamMembershipInputRequest"
}
```

Postman body template:
```json
{
  "member_id": "00000000-0000-4000-8000-000000000001",
  "role": "MEMBER"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/teams/{id}/members/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/teams/{id}/members/{membership_id}/leave/

Purpose: v1_teams_members_leave_create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Request body schema:
```json
{}
```

Postman body template:
```json
null
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/teams/{id}/members/{membership_id}/leave/`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: organization runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.

## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
