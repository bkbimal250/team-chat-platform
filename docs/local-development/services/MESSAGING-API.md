# Messaging API

Last verified: 2026-10-04. Port: 8004.

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

Postman: `GET {{messaging_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


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

Postman: `GET {{messaging_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{conversation_id}/messages

Purpose: Create

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[
  {
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
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
  "$ref": "#/components/schemas/SendMessage"
}
```

Postman body template:
```json
{
  "client_message_id": "00000000-0000-4000-8000-000000000001",
  "type": "TEXT",
  "text": "<REPLACE_WITH_VALID_VALUE>",
  "media_id": "00000000-0000-4000-8000-000000000001",
  "reply_to_message_id": "00000000-0000-4000-8000-000000000001"
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

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{conversation_id}/messages`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/conversations/{conversation_id}/messages

Purpose: History

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[
  {
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
    }
  },
  {
    "name": "before_sequence",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "Before Sequence"
    }
  },
  {
    "name": "after_sequence",
    "in": "query",
    "required": false,
    "schema": {
      "anyOf": [
        {
          "type": "integer"
        },
        {
          "type": "null"
        }
      ],
      "title": "After Sequence"
    }
  },
  {
    "name": "limit",
    "in": "query",
    "required": false,
    "schema": {
      "type": "integer",
      "default": 50,
      "title": "Limit"
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

Postman: `GET {{gateway_base_url}}/api/v1/conversations/{conversation_id}/messages`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## PATCH /api/v1/messages/{message_id}

Purpose: Edit

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[
  {
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
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
  "$ref": "#/components/schemas/EditMessage"
}
```

Postman body template:
```json
{
  "text": "<REPLACE_WITH_VALID_VALUE>"
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

Postman: `PATCH {{gateway_base_url}}/api/v1/messages/{message_id}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## DELETE /api/v1/messages/{message_id}

Purpose: Delete

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[
  {
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
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

Postman: `DELETE {{gateway_base_url}}/api/v1/messages/{message_id}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/messages/{message_id}/reactions

Purpose: Add Reaction

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[
  {
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
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
  "$ref": "#/components/schemas/ReactionInput"
}
```

Postman body template:
```json
{
  "reaction": "<REPLACE_WITH_VALID_VALUE>"
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

Postman: `POST {{gateway_base_url}}/api/v1/messages/{message_id}/reactions`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## DELETE /api/v1/messages/{message_id}/reactions/{reaction}

Purpose: Remove Reaction

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
```json
[
  {
    "name": "message_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Message Id"
    }
  },
  {
    "name": "reaction",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "title": "Reaction"
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

Postman: `DELETE {{gateway_base_url}}/api/v1/messages/{message_id}/reactions/{reaction}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{conversation_id}/delivered

Purpose: Delivered

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[
  {
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
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
  "$ref": "#/components/schemas/SequenceInput"
}
```

Postman body template:
```json
{
  "sequence": 1.0
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

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{conversation_id}/delivered`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/conversations/{conversation_id}/read

Purpose: Read

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[
  {
    "name": "conversation_id",
    "in": "path",
    "required": true,
    "schema": {
      "type": "string",
      "format": "uuid",
      "title": "Conversation Id"
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
  "$ref": "#/components/schemas/SequenceInput"
}
```

Postman body template:
```json
{
  "sequence": 1.0
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

Postman: `POST {{gateway_base_url}}/api/v1/conversations/{conversation_id}/read`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: messaging runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.