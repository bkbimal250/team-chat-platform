# Notification API

Last verified: 2026-10-04. Port: 8006.

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

Postman: `GET {{notification_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


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

Postman: `GET {{notification_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PUT /api/v1/notifications/devices/current/token

Purpose: Put Token

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/TokenRequest"
}
```

Postman body template:
```json
{
  "platform": "<REPLACE_WITH_VALID_VALUE>",
  "provider": "<REPLACE_WITH_VALID_VALUE>",
  "push_token": "<REPLACE_WITH_VALID_VALUE>"
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

Postman: `PUT {{gateway_base_url}}/api/v1/notifications/devices/current/token`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## DELETE /api/v1/notifications/devices/current/token

Purpose: Delete Token

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `DELETE {{gateway_base_url}}/api/v1/notifications/devices/current/token`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/notifications/preferences

Purpose: Get Preferences

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `GET {{gateway_base_url}}/api/v1/notifications/preferences`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/notifications/preferences

Purpose: Patch Preferences

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/PreferencePatch"
}
```

Postman body template:
```json
{
  "push_enabled": true,
  "message_notifications": true,
  "group_notifications": true,
  "notification_preview": "<REPLACE_WITH_VALID_VALUE>",
  "sound_enabled": true,
  "vibration_enabled": true
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

Postman: `PATCH {{gateway_base_url}}/api/v1/notifications/preferences`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/notifications

Purpose: List Notifications

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `GET {{gateway_base_url}}/api/v1/notifications`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: notification runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.