# Gateway API

Last verified: 2026-10-04. Port: 8008.

Commands: `python scripts/local/dev.py start`, `python scripts/local/dev.py health`. Expected: live/ready 200. Client routes use Gateway 8008; internal routes use the service directly. No AWS required.

Full request/response constraints and component definitions are in the adjacent OPENAPI.json. JSON below is a schema template; replace placeholders. A route inventory is not a claim that all destructive mutations were exercised.

Gateway hides catch-all forwarding from OpenAPI. Organization resource namespaces -> 8000; auth/devices -> 8001; users -> 8002; conversation message/delivered/read subresources and messages -> 8004; remaining conversations -> 8003; media -> 8005; notifications -> 8006. `/health/live` and `/health/ready` are served directly on 8008. Specific Messaging routes precede the Conversation catch-all.