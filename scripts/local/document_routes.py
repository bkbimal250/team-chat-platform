"""Regenerate local route reference and Postman assets from verified live OpenAPI."""

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs/local-development"
SERVICES = [
    "organization",
    "identity",
    "user",
    "conversation",
    "messaging",
    "media",
    "notification",
    "realtime",
    "gateway",
]


def resolve(schema, spec):
    if "$ref" in schema:
        value = spec
        for key in schema["$ref"].split("/")[1:]:
            value = value[key]
        return value
    return schema


def example(schema, spec, depth=0):
    schema = resolve(schema, spec)
    if depth > 5:
        return None
    if "example" in schema:
        return schema["example"]
    if "enum" in schema:
        return schema["enum"][0]
    if "anyOf" in schema:
        return example(schema["anyOf"][0], spec, depth + 1)
    kind = schema.get("type")
    if kind == "object" or "properties" in schema:
        return {
            key: example(value, spec, depth + 1)
            for key, value in schema.get("properties", {}).items()
        }
    if kind == "array":
        return [example(schema.get("items", {}), spec, depth + 1)]
    if kind == "boolean":
        return schema.get("default", True)
    if kind in {"integer", "number"}:
        return schema.get("default", schema.get("minimum", 1))
    if schema.get("format") == "uuid":
        return "00000000-0000-4000-8000-000000000001"
    if schema.get("format") == "date-time":
        return "2026-10-04T00:00:00Z"
    return schema.get("default", "<REPLACE_WITH_VALID_VALUE>")


def auth(path, operation):
    if path.startswith(("/internal/", "/api/internal/")):
        return "service token", [
            {"key": "X-Internal-Service-Token", "value": "{{internal_service_token}}"}
        ]
    public = ("/health/", "/auth/otp/", "/auth/refresh", "/auth/qr/challenges")
    if any(part in path for part in public) and not any(
        part in path for part in ("authorize", "reject", "cancel")
    ):
        return "none", []
    return "access token", [
        {"key": "Authorization", "value": "Bearer {{access_token}}"}
    ]


def main():
    (DOCS / "services").mkdir(parents=True, exist_ok=True)
    (DOCS / "postman").mkdir(exist_ok=True)
    collection = {
        "info": {
            "name": "GlobalChat Local",
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
        },
        "item": [],
    }
    rows = [
        "# Postman testing guide",
        f"Last verified: {datetime.now(UTC).date()}. Source: running local OpenAPI schemas.",
        "Import the collection/environment under `../postman/`. Examples are schema-derived templates, not working credentials. Replace placeholders and check required fields in the request schema. PARTIAL means schema/import verified, not that every mutation was executed.",
        "**YOU DO THIS MANUALLY:** request a development OTP for an explicitly seeded phone, copy `development_code` privately into verify request, then use the returned access token. Do not share the environment after tokens are captured.",
        "| Service | Method | Route | Auth | Purpose | Call through | Status |",
        "|---|---|---|---|---|---|---|",
    ]
    for index, service in enumerate(SERVICES):
        spec = json.loads((ROOT / ".local/schemas" / f"{service}.json").read_text())
        (DOCS / "services" / f"{service.upper()}-OPENAPI.json").write_text(
            json.dumps(spec, indent=2)
        )
        lines = [
            f"# {service.title()} API",
            f"Last verified: {datetime.now(UTC).date()}. Port: {8000 + index}.",
            "Commands: `python scripts/local/dev.py start`, `python scripts/local/dev.py health`. Expected: live/ready 200. Client routes use Gateway 8008; internal routes use the service directly. No AWS required.",
            "Full request/response constraints and component definitions are in the adjacent OPENAPI.json. JSON below is a schema template; replace placeholders. A route inventory is not a claim that all destructive mutations were exercised.",
        ]
        group = {"name": service.title(), "item": []}
        for path, methods in spec["paths"].items():
            for method, operation in methods.items():
                if method not in {"get", "post", "put", "patch", "delete"}:
                    continue
                token_type, headers = auth(path, operation)
                direct = path.startswith(("/internal/", "/api/internal/", "/health/"))
                base = f"{service}_base_url" if direct else "gateway_base_url"
                url = "{{" + base + "}}" + path
                params = operation.get("parameters", [])
                bodies = operation.get("requestBody", {}).get("content", {})
                body_schema = bodies.get("application/json", {}).get("schema", {})
                body = example(body_schema, spec) if bodies else None
                title = operation.get("summary", operation.get("operationId", path))
                lines += [
                    f"\n## {method.upper()} {path}",
                    f"Purpose: {title}",
                    f"Auth required: {'NO' if token_type == 'none' else 'YES'}. Token type: {token_type}.",
                    "Required headers: "
                    + json.dumps(
                        headers
                        + (
                            [{"key": "Content-Type", "value": "application/json"}]
                            if bodies
                            else []
                        )
                    ),
                    "Path/query parameters:\n```json\n"
                    + json.dumps(params, indent=2)
                    + "\n```",
                    "Request body schema:\n```json\n"
                    + json.dumps(body_schema, indent=2)
                    + "\n```",
                    "Postman body template:\n```json\n"
                    + json.dumps(body, indent=2)
                    + "\n```",
                    "Success/error responses (actual schema):\n```json\n"
                    + json.dumps(operation.get("responses", {}), indent=2)
                    + "\n```",
                    "Common authorization failures: 401 missing/invalid token; 403 tenant/permission denied. Validation errors use the service's actual error envelope. Do not bypass authorization.",
                    f"Postman: `{method.upper()} {url}`. Set headers above; replace path IDs and body values, send, inspect HTTP response and correlation ID. Dependencies: {service} runtime, its database where applicable, Redis/RabbitMQ for event/session features. Internal service-token calls are operator-only.",
                ]
                rows.append(
                    f"| {service} | {method.upper()} | `{path}` | {token_type} | {title} | {'DIRECT SERVICE' if direct else 'THROUGH GATEWAY'} | PARTIAL |"
                )
                request = {
                    "method": method.upper(),
                    "header": headers,
                    "url": url,
                    "description": f"{title}. Replace schema placeholders. See services/{service.upper()}-API.md.",
                }
                if bodies:
                    request["header"].append(
                        {"key": "Content-Type", "value": "application/json"}
                    )
                    request["body"] = {
                        "mode": "raw",
                        "raw": json.dumps(body, indent=2),
                        "options": {"raw": {"language": "json"}},
                    }
                group["item"].append(
                    {"name": f"{method.upper()} {path}", "request": request}
                )
        if service == "gateway":
            lines += [
                "Gateway hides catch-all forwarding from OpenAPI. Organization resource namespaces -> 8000; auth/devices -> 8001; users -> 8002; conversation message/delivered/read subresources and messages -> 8004; remaining conversations -> 8003; media -> 8005; notifications -> 8006. `/health/live` and `/health/ready` are served directly on 8008. Specific Messaging routes precede the Conversation catch-all."
            ]
        if service == "realtime":
            lines += [
                "WebSocket: `ws://localhost:8007/api/v1/realtime?token=<ACCESS_TOKEN>`. Token must contain valid RS256 org/member/session/device claims. Client frames have version 1; subscribe/unsubscribe and typing.start/typing.stop require conversation_id. See testing/WEBSOCKET-TESTING.md. Never paste real tokens in shared screenshots."
            ]
        (DOCS / "services" / f"{service.upper()}-API.md").write_text("\n\n".join(lines))
        collection["item"].append(group)
    (DOCS / "testing").mkdir(exist_ok=True)
    (DOCS / "testing/POSTMAN-TESTING-GUIDE.md").write_text("\n\n".join(rows))
    (DOCS / "postman/GlobalChat-Local.postman_collection.json").write_text(
        json.dumps(collection, indent=2)
    )
    values = [
        {
            "key": f"{s}_base_url",
            "value": f"http://localhost:{8000 + i}",
            "enabled": True,
        }
        for i, s in enumerate(SERVICES)
    ]
    values += [
        {
            "key": key,
            "value": "",
            "enabled": True,
            "type": "secret" if "token" in key else "default",
        }
        for key in [
            "access_token",
            "refresh_token",
            "internal_service_token",
            "organization_id",
            "user_id",
            "member_id",
            "conversation_id",
            "message_id",
            "media_id",
            "device_id",
        ]
    ]
    (DOCS / "postman/GlobalChat-Local.postman_environment.json").write_text(
        json.dumps(
            {
                "name": "GlobalChat Local",
                "values": values,
                "_postman_variable_scope": "environment",
            },
            indent=2,
        )
    )
    print("Nine API references and Postman assets generated from actual schemas")


if __name__ == "__main__":
    main()
