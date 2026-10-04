# User API

Last verified: 2026-10-04. Port: 8002.

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

Postman: `GET {{user_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


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

Postman: `GET {{user_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /internal/v1/users/block-check

Purpose: Block Check

Auth required: YES. Token type: service token.

Required headers: [{"key": "X-Internal-Service-Token", "value": "{{internal_service_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/BlockCheck"
}
```

Postman body template:
```json
{
  "user_a_id": "00000000-0000-4000-8000-000000000001",
  "user_b_id": "00000000-0000-4000-8000-000000000001"
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

Postman: `POST {{user_base_url}}/internal/v1/users/block-check`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /internal/v1/users/projections

Purpose: Projections

Auth required: YES. Token type: service token.

Required headers: [{"key": "X-Internal-Service-Token", "value": "{{internal_service_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/ProjectionRequest"
}
```

Postman body template:
```json
{
  "user_ids": [
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

Postman: `POST {{user_base_url}}/internal/v1/users/projections`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/me

Purpose: Me

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

Postman: `GET {{gateway_base_url}}/api/v1/users/me`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/users/me

Purpose: Update Me

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/ProfilePatch"
}
```

Postman body template:
```json
{
  "display_name": "<REPLACE_WITH_VALID_VALUE>",
  "avatar_media_id": "00000000-0000-4000-8000-000000000001",
  "about": "<REPLACE_WITH_VALID_VALUE>"
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

Postman: `PATCH {{gateway_base_url}}/api/v1/users/me`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/me/preferences

Purpose: Preferences

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

Postman: `GET {{gateway_base_url}}/api/v1/users/me/preferences`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/users/me/preferences

Purpose: Update Preferences

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/SettingsPatch"
}
```

Postman body template:
```json
{
  "language": "<REPLACE_WITH_VALID_VALUE>",
  "timezone": "<REPLACE_WITH_VALID_VALUE>",
  "theme_preference": "<REPLACE_WITH_VALID_VALUE>",
  "enter_to_send": true,
  "media_auto_download": true,
  "link_preview_enabled": true
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

Postman: `PATCH {{gateway_base_url}}/api/v1/users/me/preferences`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/users/{user_id}/block

Purpose: Block

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `POST {{gateway_base_url}}/api/v1/users/{user_id}/block`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## DELETE /api/v1/users/{user_id}/block

Purpose: Unblock

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `DELETE {{gateway_base_url}}/api/v1/users/{user_id}/block`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/me/privacy

Purpose: Privacy

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

Postman: `GET {{gateway_base_url}}/api/v1/users/me/privacy`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/users/me/privacy

Purpose: Update Privacy

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/PrivacyPatch"
}
```

Postman body template:
```json
{
  "profile_photo_visibility": "<REPLACE_WITH_VALID_VALUE>",
  "about_visibility": "<REPLACE_WITH_VALID_VALUE>",
  "online_status_visibility": "<REPLACE_WITH_VALID_VALUE>",
  "last_seen_visibility": "<REPLACE_WITH_VALID_VALUE>",
  "read_receipts_enabled": true
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

Postman: `PATCH {{gateway_base_url}}/api/v1/users/me/privacy`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/me/blocked

Purpose: Blocked Users

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

Postman: `GET {{gateway_base_url}}/api/v1/users/me/blocked`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/search

Purpose: Search Users

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `GET {{gateway_base_url}}/api/v1/users/search`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/users/{user_id}

Purpose: Get Profile

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Postman: `GET {{gateway_base_url}}/api/v1/users/{user_id}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: user runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.

## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
