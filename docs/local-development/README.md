Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# GlobalChat local development
Start with [setup](01-LOCAL-SETUP.md), then [authentication](04-AUTHENTICATION.md) and [Postman](testing/POSTMAN-TESTING-GUIDE.md). API references and full schemas are under services/. Actual verification results are under status/.

No AWS/Terraform commands are required. Existing service boundaries and production authentication rules remain intact.

Admin panel: [real local API integration](admin/README.md).

## Complete source-backed reference (2026-10-05)

- [Nine service references](services/README.md): 152 method/path operations, including internal and signed-storage routes and the WebSocket contract.
- [Fourteen ordered manual-testing chapters](manual-testing/README.md).
- [Actual ports](architecture/SERVICE-PORTS.md), [frontend routing](architecture/FRONTEND-GATEWAY-FLOW.md), [database ownership](03-DATABASES.md), and [events](architecture/EVENT-FLOWS.md).
- [Postman collection](postman/GlobalChat-Local.postman_collection.json) and [environment template](postman/GlobalChat-Local.postman_environment.json).

Requests use real contracts and private placeholders. An endpoint being documented does not mean its mutation has been executed. Use disposable local fixtures, one request at a time, and verify the active OTP provider before any OTP request. Existing specialized admin/onboarding guides remain available.

Primary local authentication: [Email + Password](onboarding/EMAIL-PASSWORD-AUTH.md). Older OTP onboarding examples are preserved for explicitly enabled future testing.
