# Company workspace

Company registration remains POST /api/v1/auth/registration/company, creating a durable onboarding intent, User profile, Organization and OWNER membership before tenant session issuance. Existing personal users cannot yet create a new company through this registration endpoint; it returns ACCOUNT_EXISTS. Existing-user company creation is Phase 4.

Email-bound invitation acceptance handles existing and new identities, persists retryable intent and enforces expiry/revocation/single use and authoritative organization/role. Existing identities/profiles are reused. One identity may hold multiple memberships; /auth/context selects an active membership. Organization OWNER/ADMIN/MEMBER roles are separate from PlatformGrant ADMIN/SUPER_ADMIN.

Personal accounts carry no company permissions. Company UI resources load only in an authorized tenant context. Company group owner/admin-only creation is a separate pending authorization phase.
