# Conversation API

Last verified: 2026-10-04. Port: 8003.

Commands: `python scripts/local/dev.py start`, `python scripts/local/dev.py health`. Expected: live/ready 200. Client routes use Gateway 8008; internal routes use the service directly. No AWS required.

Full request/response constraints and component definitions are in the adjacent OPENAPI.json. JSON below is a schema template; replace placeholders. A route inventory is not a claim that all destructive mutations were exercised.


## GET /health/live

Purpose: Live

Auth required: NO. Token type: none.

Required headers: []

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
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {}
      }
    }
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{conversation_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /health/ready

Purpose: Ready

Auth required: NO. Token type: none.

Required headers: []

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
    "description": "Successful Response",
    "content": {
      "application/json": {
        "schema": {}
      }
    }
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{conversation_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/direct

Purpose: Direct

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/DirectIn"
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/direct`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/groups

Purpose: Group

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/GroupIn"
}
```

Postman body template:
```json
{
  "title": "<REPLACE_WITH_VALID_VALUE>",
  "description": "<REPLACE_WITH_VALID_VALUE>",
  "member_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/groups`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/conversations

Purpose: List Conversations

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/conversations`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/conversations/{cid}

Purpose: Get

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/conversations/{cid}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/conversations/{cid}

Purpose: Update

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/UpdateConversation"
}
```

Postman body template:
```json
{
  "title": "<REPLACE_WITH_VALID_VALUE>",
  "description": "<REPLACE_WITH_VALID_VALUE>",
  "avatar_media_id": "00000000-0000-4000-8000-000000000001"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/conversations/{cid}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/members

Purpose: Add

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/MemberIds"
}
```

Postman body template:
```json
{
  "member_ids": [
    "00000000-0000-4000-8000-000000000001"
  ]
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/members`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/conversations/{cid}/members

Purpose: Members

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/conversations/{cid}/members`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## DELETE /api/v1/conversations/{cid}/members/{mid}

Purpose: Remove

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `DELETE {{gateway_base_url}}/api/v1/conversations/{cid}/members/{mid}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/leave

Purpose: Leave

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/leave`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/close

Purpose: Close

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/close`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/members/{mid}/promote

Purpose: Promote

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/members/{mid}/promote`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/members/{mid}/demote

Purpose: Demote

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/members/{mid}/demote`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{cid}/transfer-ownership

Purpose: Transfer

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/Transfer"
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{cid}/transfer-ownership`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/conversations/{cid}/state

Purpose: State

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/StateIn"
}
```

Postman body template:
```json
{
  "is_archived": true,
  "is_pinned": true,
  "muted_until": "2026-10-04T00:00:00Z",
  "is_muted_forever": true,
  "notification_level": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `PATCH {{gateway_base_url}}/api/v1/conversations/{cid}/state`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /internal/v1/conversations/{cid}/authorize

Purpose: Authorize Send

Auth required: YES. Token type: service token.

Required headers: [{"key": "X-Internal-Service-Token", "value": "{{internal_service_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "type": "object",
  "additionalProperties": true,
  "title": "Body"
}
```

Postman body template:
```json
{}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{conversation_base_url}}/internal/v1/conversations/{cid}/authorize`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: conversation runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.