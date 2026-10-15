# Personal accounts — Phase 1

POST /api/v1/auth/registration/personal accepts display_name (2–200), canonical email, international phone, password (12–128) and the existing device payload. It provisions one Identity and one User profile/preferences/privacy without creating an Organization, membership or role. Argon2id, email/phone uniqueness, existing registration rate limits and duplicate-safe errors apply. Phone association is not proof of ownership: phone_verified remains false. Email verification is separate.

A durable personal_registrations intent is committed before the internal User provision call. Failed provisioning retries with the same credentials/name/phone resume the same identity; the profile endpoint is idempotent. Activation, completion and session issuance commit together. Completed registration requires normal login.

Personal login is independent of Organization availability. Completed personal accounts without an explicitly requested organization receive personal sessions. An explicitly requested workspace requires an active authoritative membership. Existing company and platform login behavior remains unchanged.

Migration: Identity 0009_personal_accounts follows 0008_email_verification. Sessions may have NULL organization_id/member_id together; partial context is forbidden by a physical check constraint. Personal JWTs omit org/mid. Identity verifies exact persisted session/device ownership and context; User permits signed personal tokens for self profile/preferences/privacy. Tenant services retain their tenant requirements. Downgrade refuses to discard personal accounts or sessions or invent tenant IDs.

Web /register defaults to Personal Account and offers Create a Company. Personal accounts can use Profile, Settings and Devices. The home screen honestly marks personal messaging unavailable. Workspace-only screens and notifications remain unavailable without workspace context. No arbitrary people directory is exposed.

Personal → existing-user company creation is Phase 4, not implemented here. Email/password invitation acceptance reuses an existing identity; active membership switching remains available through /auth/context. Personal contacts/chat belong to Phases 2–3. Local development sends no email or SMS.

Local verification: `python -m scripts.local.verify_personal_accounts` creates one local synthetic personal account, exercises real Gateway self-service and access denial, and closes its sessions. It prints no credentials/tokens and calls no email/SMS provider. Account/profile remain as local smoke-test data.
