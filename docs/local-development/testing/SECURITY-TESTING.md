Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Security verification
Full existing JWT/tenant/block/media/device/QR test suites run without weakening policy. API docs list internal service-token routes separately; they must not be exposed as public cross-tenant APIs.

YOU DO THIS MANUALLY: remove Authorization; send invalid/expired JWT; use another organization token against a known conversation/message/media ID; try a non-member subscription; try another user's device ID; replay client_message_id and consumed QR. Expect 401/403/404 according to domain contract (some required Header inputs currently return 422). Never use DEV_CONTEXT_ENABLED or fabricated signed JWT to bypass real authorization.
