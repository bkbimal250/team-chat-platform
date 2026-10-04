# Identity API

Last verified: 2026-10-04. Port: 8001.

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

Postman: `GET {{identity_base_url}}/health/live`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


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

Postman: `GET {{identity_base_url}}/health/ready`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/otp/request

Purpose: Otp Request

Auth required: NO. Token type: none.

Required headers: [{"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/OTPRequest"
}
```

Postman body template:
```json
{
  "phone_number": "<REPLACE_WITH_VALID_VALUE>",
  "purpose": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/otp/request`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/otp/verify

Purpose: Otp Verify

Auth required: NO. Token type: none.

Required headers: [{"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/OTPVerifyRequest"
}
```

Postman body template:
```json
{
  "challenge_id": "00000000-0000-4000-8000-000000000001",
  "code": "<REPLACE_WITH_VALID_VALUE>",
  "device": {
    "installation_id": "<REPLACE_WITH_VALID_VALUE>",
    "platform": "ANDROID",
    "device_name": "<REPLACE_WITH_VALID_VALUE>",
    "device_model": "<REPLACE_WITH_VALID_VALUE>",
    "os_version": "<REPLACE_WITH_VALID_VALUE>",
    "app_version": "<REPLACE_WITH_VALID_VALUE>"
  },
  "organization_id": "00000000-0000-4000-8000-000000000001"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/otp/verify`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/refresh

Purpose: Refresh

Auth required: NO. Token type: none.

Required headers: [{"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/RefreshRequest"
}
```

Postman body template:
```json
{
  "refresh_token": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/refresh`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/logout

Purpose: Logout

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
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
      }
    }
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/logout`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/logout-all

Purpose: Logout All

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
        "schema": {
          "$ref": "#/components/schemas/RevokeResponse"
        }
      }
    }
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/logout-all`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/context

Purpose: Switch Context

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/ContextRequest"
}
```

Postman body template:
```json
{
  "organization_id": "00000000-0000-4000-8000-000000000001"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/context`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/auth/me

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
        "schema": {
          "$ref": "#/components/schemas/MeResponse"
        }
      }
    }
  }
}
```

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/auth/me`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/qr/challenges

Purpose: Qr Create

Auth required: NO. Token type: none.

Required headers: [{"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
```json
[]
```

Request body schema:
```json
{
  "$ref": "#/components/schemas/QRCreateRequest"
}
```

Postman body template:
```json
{
  "installation_id": "<REPLACE_WITH_VALID_VALUE>",
  "platform": "ANDROID",
  "device_name": "<REPLACE_WITH_VALID_VALUE>",
  "device_model": "<REPLACE_WITH_VALID_VALUE>",
  "os_version": "<REPLACE_WITH_VALID_VALUE>",
  "app_version": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/qr/challenges`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/auth/qr/challenges/{challenge_id}/status

Purpose: Qr Status

Auth required: NO. Token type: none.

Required headers: []

Path/query parameters:
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

Postman: `GET {{gateway_base_url}}/api/v1/auth/qr/challenges/{challenge_id}/status`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/qr/challenges/{challenge_id}/authorize

Purpose: Qr Authorize

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}, {"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/QRAuthorizeRequest"
}
```

Postman body template:
```json
{
  "secret": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/qr/challenges/{challenge_id}/authorize`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/qr/challenges/{challenge_id}/consume

Purpose: Qr Consume

Auth required: NO. Token type: none.

Required headers: [{"key": "Content-Type", "value": "application/json"}]

Path/query parameters:
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

Request body schema:
```json
{
  "$ref": "#/components/schemas/QRConsumeRequest"
}
```

Postman body template:
```json
{
  "secret": "<REPLACE_WITH_VALID_VALUE>"
}
```

Success/error responses (actual schema):
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/qr/challenges/{challenge_id}/consume`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/devices

Purpose: Devices

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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/devices`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/devices/{device_id}

Purpose: Device

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/devices/{device_id}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/devices/{device_id}/revoke

Purpose: Revoke Device

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/devices/{device_id}/revoke`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## GET /api/v1/auth/sessions

Purpose: Sessions

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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `GET {{gateway_base_url}}/api/v1/auth/sessions`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.


## POST /api/v1/auth/sessions/{session_id}/revoke

Purpose: Revoke

Auth required: YES. Token type: access token.

Required headers: [{"key": "Authorization", "value": "Bearer {{access_token}}"}]

Path/query parameters:
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

Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.

Postman: `POST {{gateway_base_url}}/api/v1/auth/sessions/{session_id}/revoke`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: identity runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.

## Company owner onboarding

See [company registration](../onboarding/COMPANY-REGISTRATION.md), [actual contracts](../onboarding/COMPANY-REGISTRATION-API.md) and [manual/automated sequence](../onboarding/COMPANY-REGISTRATION-TESTING.md). Public Gateway endpoints are POST `/api/v1/auth/registration/company/start`, `/verify`, `/resend` under that prefix. Company signup verifies phone OTP, then creates a NEW organization and real Owner membership; member invite-only policy remains intact. Registration -> OTP -> verify -> profile/current organization -> admin -> logout -> normal LOGIN OTP restores the same membership. No production deployment or real SMS was performed.
