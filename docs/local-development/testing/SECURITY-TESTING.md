Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Security verification
Full existing JWT/tenant/block/media/device/QR test suites run without weakening policy. API docs list internal service-token routes separately; they must not be exposed as public cross-tenant APIs.

## Platform administration C1

`/api/v1/platform/*` requires a valid Identity session **and** an active persistent platform grant. Tenant roles are deliberately ignored. Security tests cover no-token `401`, tenant MEMBER/ADMIN/OWNER `403`, a grant's permissions, revocation fail-closed behavior, and response allowlists that exclude password hashes and phone values. Platform organization requests are also bounded, filtered and separately authorized; existing tenant paths remain tenant-scoped.

YOU DO THIS MANUALLY: remove Authorization; send invalid/expired JWT; use another organization token against a known conversation/message/media ID; try a non-member subscription; try another user's device ID; replay client_message_id and consumed QR. Expect 401/403/404 according to domain contract (some required Header inputs currently return 422). Never use DEV_CONTEXT_ENABLED or fabricated signed JWT to bypass real authorization.
