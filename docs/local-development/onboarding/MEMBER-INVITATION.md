> Preserved phone OTP reference: disabled in the current primary flow. Use [email/password authentication](EMAIL-PASSWORD-AUTH.md) for normal local registration/login. Enable OTP explicitly only for future capability tests.

# Secure member invitation and employee onboarding

Local development only. Admin: http://localhost:3000. Employee web: http://localhost:3001. All browser API calls use Gateway http://localhost:8008. No paid SMS, email, push or cloud deployment.

## Trust and storage

Organization owns invitations, role assignments and tenant/branch/team memberships. Identity owns OTP challenges, globally unique normalized phones, devices/sessions and durable `invitation_onboardings`. User owns profiles. Internal HTTP provisioning uses the existing shared service authentication boundary; it is not forwarded by Gateway. No service writes another service's database.

Invitation creation derives tenant/inviter from the authenticated JWT and checks current backend permissions. OWNER and ADMIN can invite; MANAGER may invite only roles it can delegate. MEMBER cannot invite. Current role permissions are rechecked under the tenant lock at acceptance. Removed/suspended inviters, inactive tenants/targets and changed role delegation fail closed. Existing inactive memberships are not reactivated. Existing active memberships are reused without changing their role/branch/team assignments.

Phones are normalized to E.164. Email is optional contact data and is never proof of ownership. Tokens use 32 cryptographically random bytes, URL-safe encoding and SHA-256 storage. Only create/resend returns a transient local development link. Lists/retrieval never return plaintext tokens or hashes. Public validation returns company/name, masked phone and expiry; no internal IDs or contact details. Fragment links `/join#invite=...` keep secrets out of web access logs/referrers. The page clears the fragment immediately, disables indexing and uses no-referrer metadata. Secrets are not stored in browser storage or analytics.

## Lifecycle

`PENDING -> ACCEPTED | REVOKED | EXPIRED`. `INVITATION_TTL_HOURS` defaults to 48; recipient invitations cannot extend beyond that bound. Clock expiration is enforced at validation/acceptance and represented in list/filter responses; a subsequent new invitation expires the old physical pending row. Same phone/current tenant/pending invitation returns controlled `INVITATION_PENDING`; active accepted membership returns `MEMBER_ALREADY_EXISTS`. Expired/revoked recipients can receive a fresh invitation. The same global phone can join different organizations.

Resend rotates the token on the same invitation, invalidating the old link immediately. It creates no membership. Revocation requires backend permission and a UI confirmation; only pending invitations can be revoked. Accepted membership removal is a separate command. Legacy pre-recipient invitation operations remain compatible, but the legacy admin accept endpoint refuses phone-bound employee invitations: recipient OTP is mandatory.

## OTP and provisioning saga

1. Identity validates the token through authenticated Organization HTTP and obtains the authoritative phone/tenant/name.
2. Existing `OTPService` requests an INVITATION-purpose challenge, with the existing per-IP/per-phone rate limits, 60-second cooldown, five attempts and 300-second OTP TTL. The local provider exposes a development code intentionally in the response/UI. No paid delivery is performed.
3. Verification accepts only `onboarding_id`, `otp`, `device`. Phone/tenant/role/branch/team inputs are forbidden. The stored challenge must match the authoritative phone and purpose. Failed attempts/locks are committed.
4. Successful OTP commits a VERIFIED intent and reserves/reuses a global Identity. Existing active identities/profiles are retained. An identity reserved by another verified invitation can be reused after another valid phone proof; a company-registration reservation or disabled account is not adopted.
5. User idempotently provisions a profile without overwriting existing names. Organization accepts under tenant/invitation locks, validates token hash/phone/current authority and creates at most one active member and the stored role/branch/team assignments. Audit/outbox changes share the transaction.
6. Only confirmed acceptance activates a new Identity and issues the existing normal session/tokens. An existing active Identity does not emit another identity-created event. The intent becomes COMPLETED and its verified-code hash is cleared.

Cross-service failures leave a durable VERIFIED intent. Resume is bounded to 30 minutes and five code attempts. Retry with the same verified code; it does not send another OTP. Reopening the original link and requesting continuation returns the same VERIFIED challenge. Even if Organization already committed acceptance before Identity session completion, its private `resume` contract allows only the identical hash, phone and identity; public accepted-token replay after completion remains rejected. Network retries and parallel tabs serialize; completed replay returns a safe sign-in response. No permanent invitation-based authentication is created.

One session has one active organization/member context. Existing context switching remains available for multi-organization identities; no global one-organization-per-phone restriction is added.

## Events and chat access

Existing member.created/activated/role_changed.v2 and branch_membership/team_membership.created.v1 events are emitted atomically, along with invitation.created/accepted/revoked.v1. Resend re-emits invitation.created.v1 with non-sensitive `delivery_rotated` metadata. Tokens, recipient phones, OTPs and email never enter event payloads. User provisioning and existing identity/member consumers use their established idempotency/ProcessedEvent boundaries. Rabbit redelivery does not duplicate a profile/membership.

Membership does not add the employee to private conversations. Workspace people search resolves real member IDs; existing conversation and messaging membership authorization and user block policy remain authoritative. Messaging may briefly reject a newly created conversation until its authorization projection consumes the event; wait/retry rather than bypassing authorization.

## Configuration and migrations

Organization: `WEB_APP_BASE_URL=http://localhost:3001`, `INVITATION_TTL_HOURS=48`. Development delivery requires a loopback HTTP base URL and ENVIRONMENT local/test. Other environments fail closed until a real delivery provider is configured.

Organization migration: `invitations.0002_recipient_onboarding` after invitations.0001_initial. Identity migration: `0004_invitation_onboarding` after `0003_company_registration`. Both applied against the isolated Docker PostgreSQL on 5434 and repeated to prove head idempotency. Prior histories are unchanged.

See MEMBER-INVITATION-API.md and MEMBER-INVITATION-TESTING.md for exact contracts and commands.
