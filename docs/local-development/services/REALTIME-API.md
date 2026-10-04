# Realtime API

Last verified: 2026-10-04. Port: 8007.

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

Postman: `GET {{realtime_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: realtime runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


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

Postman: `GET {{realtime_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: realtime runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.

WebSocket: `ws://localhost:8007/api/v1/realtime?token=<ACCESS_TOKEN>`. Token must contain valid RS256 org/member/session/device claims. Client frames have version 1; subscribe/unsubscribe and typing.start/typing.stop require conversation_id. See testing/WEBSOCKET-TESTING.md. Never paste real tokens in shared screenshots.