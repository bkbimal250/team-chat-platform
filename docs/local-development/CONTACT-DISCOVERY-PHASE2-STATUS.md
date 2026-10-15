# Contact discovery Phase 2 — validation status

Date: 2026-10-10. Local development only.

Contact model, authenticated CRUD/match, privacy/block suppression, canonical keyed matching, and manual web contact management: implemented.
No organization-less conversation, messaging, realtime or media changes. No global directory and no admin contact-book viewer.

## Regression

| Backend | Passed | Failed |
|---|---:|---:|
| organization | 78 | 0 |
| identity | 174 | 0 |
| user | 61 | 0 |
| conversation | 20 | 0 |
| messaging | 71 | 0 |
| media | 47 | 0 |
| notification | 50 | 0 |
| realtime | 35 | 0 |
| gateway | 38 | 0 |

Backend total: 574 passed, 0 failed. Web: 93 passed, 0 failed. Admin: 55 passed, 0 failed. Both frontends: lint, typecheck and production build PASS. Affected Identity/User Ruff checks PASS.

## Local database and runtime evidence

- Identity head 0010_contact_phone_index; User head 0003_contacts.
- Real PostgreSQL column/index inspection PASS. Both upgrade reruns PASS.
- Empty local contact-table downgrade/upgrade exercised before creating any contact records; no existing contact data removed.
- Existing Identity phone index backfilled; repeat backfill safe.
- Initial real Gateway smoke: 37 successful assertions; repeat: 32 (five accounts reused). A/B personal, C hidden, D blocking, E company.
- Safe eligible fields, unknown/hidden/blocked equivalence, foreign read/update denial, private labels, company contact ownership and unchanged organization verified.
- All nine local API readiness endpoints 200; /contacts at localhost:3001 returns 200.
- UI component tests exercise actual form, country input, international normalization, list/CRUD, limits, error handling, and personal Contacts navigation. Responsive layout and theme tokens implemented; physical-device/browser visual QA was not performed.
- No provider sends, AWS, Terraform, VPS or production changes.

## Phase 2 files

Backend: Identity config, models, phone normalizer, contact_phone.py, internal contact_discovery.py, contact_phone_backfill.py, main router, tests; User main model/privacy/router, contacts.py, contacts_runtime.py, pyproject.toml/uv.lock, tests; Gateway route map/tests.
Web: app/contacts layout/page, features/contacts API/UI, workspace navigation, shared country input, privacy settings, People label, personal welcome, Retry-After handling, contact/settings/personal navigation tests.
Admin: no source changes.
Configuration: root and Identity .env.example placeholders; User .env.example; existing Docker Compose Identity key/User dependency wiring; local runner dedicated ignored key generation.
Migrations: Identity 0010_contact_phone_index; User 0003_contacts.
Docs: CONTACT-DISCOVERY.md, this status, USER/GATEWAY API notes, Identity/User OpenAPI, Postman collection/environment. Local smoke script scripts/local/verify_contacts.py. Private test fixture/config remains Git-ignored.

## Operational limitations

Unverified phones are associations, not proof of ownership. Their status is exposed truthfully. The shared peer-IP quota behind a Gateway is deliberately conservative; no untrusted forwarded header is accepted by the application. Key rotation requires a planned re-index and contact re-entry/versioned migration; see CONTACT-DISCOVERY.md. Contacts avatar references are exposed only for EVERYONE visibility.

Known deferred work: Phase 3 personal chat and tenant-independent Conversation/Messaging/Realtime/Media authorization; existing-user company creation; company group/team role enforcement; production invitation email.
