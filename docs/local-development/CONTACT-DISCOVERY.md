# Contact discovery — Phase 2

## Audit and boundaries
PASS: Identity canonical E.164 storage and unique phone constraint; authenticated personal accounts; User mutual block model; tenant-restricted workspace search; existing Gateway bridge.
PARTIAL: phone association is present but unverified; profile visibility does not prove phone ownership.
MISSING (now implemented): private contacts, exact phone index, discoverability control, bounded matching, Contacts UI.
CONFLICT: the brief assumed a discoverability flag already existed. The actual UserPrivacySettings had visibility controls only. One discoverable boolean was added to that same model.

Personal contacts are owned by User.id, never by organization or member. Company directory remains separate and is labelled Workspace Members. No global phone/name/email/prefix directory, no platform contact-book browser, no personal chat or tenant-auth changes.

## Representation and policy
Identity retains its existing unique canonical phone for account purposes. Contact books persist only HMAC-SHA256(CONTACT_MATCHING_SECRET, canonical E.164), private local label, owner and timestamps. No raw contact phone, suffix, organization or cached matched identity is stored. The dedicated matching key exists only on Identity servers. User obtains opaque digests over the authenticated internal service boundary.

Active, non-deleted identities may be matched even when phone_verified=false. This is an account association, NOT proof that the user owns that number. The UI explicitly marks unverified associations; no SMS verification was added or faked. The active User must have discoverable=true and neither side may block the other. Missing privacy rows fail closed. Every saved-contact read rechecks the current Identity mapping, User status, discoverability and both block directions.

Eligible profiles expose only user_id, display_name, phone_verified, and avatar_media_id when visibility is EVERYONE. ORGANIZATION/CONTACTS/NOBODY avatar settings remain conservatively hidden in this personal discovery flow. Unknown, hidden, blocked, inactive and self matches all use matched_user:null without reasons or target identifiers. Local labels are returned only to their owner and never update a profile.

## Actual public API (Gateway -> User)
All routes require the existing signed bearer token, with or without a complete company context. No caller-supplied owner/target identifier is accepted.

- POST /api/v1/contacts: {"phone":"2025550123","country":"US","local_label":"Example contact"}. Idempotent for owner/canonical phone. An explicit label updates that owner's label; omitted label preserves it.
- GET /api/v1/contacts?limit=20&after=<last UUID>: owned items and next_cursor; limit 1..50. No search or arbitrary owner filter.
- GET /api/v1/contacts/{id}: owned entry, refreshed eligibility.
- PATCH /api/v1/contacts/{id}: local_label (nullable), and optional replacement phone plus country. Replacement re-resolves matching; duplicate conflict is 409.
- DELETE /api/v1/contacts/{id}: removes only that owner's contact entry.
- POST /api/v1/contacts/match: {"contacts":[{"phone":"+12025550123"}]}. 1..20 inputs, exact canonical deduplication, results keyed by first input_index; no persistence.
- GET/PATCH /api/v1/users/me/privacy now includes discoverable. Existing privacy fields remain unchanged.

Unavailable/foreign IDs: 404. Invalid fields/batches: 422 without input echo. Quotas: 429 plus Retry-After seconds. Identity/Redis unavailable: 503, no permissive fallback. No bodies, phones, digests or labels are logged/audited by these endpoints. Internal /internal/v1/contact-discovery is service-token protected, absent from public Gateway routing and OpenAPI.

## Enumeration controls
Redis atomic fixed windows: 60 requests/minute per identity; 120/minute per observed peer IP; submitted numbers 50/hour per identity and 100/hour per peer IP. Match/create/phone replacement spend number budget before normalization/lookup; repeats and invalid numbers do not bypass it. Redis keys use contacts:requests:{identity|ip}:* and contacts:numbers:{identity|ip}:*, TTL 60/3600 seconds. Redis failure fails closed. Arbitrary X-Forwarded-For is not trusted. Behind a shared Gateway, the observed peer quota is deliberately conservative and shared; trusted forwarding per-client limits may be added later with explicit proxy trust configuration. No quota resets are needed for deployment.

## Schema and operation
Identity: 0010_contact_phone_index after 0009_personal_accounts; unique indexed contact_phone_digest. User: 0003_contacts after 0002_outbox_delivery_state; contacts.owner_user_id FK users.id, UNIQUE(owner_user_id,phone_digest), index(owner_user_id,id), discoverable boolean default true. Concurrent contact adds use PostgreSQL ON CONFLICT. Both migrations have downgrade implementations; downgrading User removes contact data and must not be used on populated books without explicit authorization/backup.

Deployment order (not deployed): back up, supply key to Identity processes, run each service's `python -m alembic upgrade head`, then in Identity run `python -m app.contact_phone_backfill`, then restart APIs. Backfill processes bounded 200-row transactions; fills only NULL indexes, is restart-safe and idempotent. Invalid legacy phones or canonical collisions halt; never merge identities. All phone writes must use Identity ORM/canonical normalization; arbitrary SQL bypasses index maintenance and is unsupported.

Local runner: `python -m scripts.local.dev prepare` creates the random key in ignored .local/config.json and injects it only into Identity. Existing docker-compose.yml consumes CONTACT_MATCHING_SECRET, and User receives REDIS_URL/IDENTITY_SERVICE_URL/internal token. VPS uses private Compose DNS names and its own environment-supplied key, not the local key. No cloud dependency was introduced; no VPS/AWS deployment was performed.

### Key rotation
Use a separate random key (at least 32 characters; 48 random bytes recommended) per environment, protected alongside DB backups. Never use a JWT/service token as the matching key. Do not change the key casually: contact digests cannot be re-keyed without the original numbers. A planned rotation must stop matching, rebuild the Identity index under the new key and require owners to re-enter/reimport saved contact numbers (or first implement a reviewed versioned dual-key migration). Old contact digests must never silently point to new identities. Restoring databases requires the matching key used by that snapshot. There is no raw-phone recovery from a contact book.

## Web and manual checks
Open /contacts signed in as a personal or company account. Search the country selector, enter a complete number and optional private name, save, edit the private label or replace the number, and confirm removal. Contacts uses the existing Next Gateway bridge, session refresh, accessible native confirmation dialog, Aurora light/dark tokens and responsive stacked/two-column layout. Unavailable results never identify privacy reasons. No chat button or fake conversations.

Existing privacy settings now offer Allow exact phone contact discovery. /workspace member directory remains organization-authorized and separate.

## Verification
Backend coverage includes international normalization, keyed hashing, DB canonical uniqueness, inactive/changed phone index, service authentication, bounded requests, real Redis atomic quotas/TTL and fail-closed errors, DB concurrent deduplication, fresh privacy/block checks, cross-owner CRUD denial, private label isolation and minimal avatar response. Frontend coverage includes real-contract requests, list/add/edit/delete, neutral result, invalid phone, limits and failure preservation. Local `scripts/local/verify_contacts.py` runs real Gateway requests for A/B personal, C hidden, D blocking, E company; credentials remain ignored in .local, no external provider calls.

Phase 3 remains required for organization-less conversation/message/realtime/media authorization. Existing-user company creation, company group/team role enforcement and production invitation email remain later work.
