# Platform administration API matrix

Code inspection baseline: 2026-10-05. Tenant OWNER/ADMIN permissions are not platform grants. Existing tenant APIs remain unchanged. Status refers to suitability for platform administration, not availability to company users.

| Service | Method | Path | Purpose | Auth | Platform permission | Read/Write | Sensitive data | Gateway route | Status |
|---|---|---|---|---|---|---|
| Identity | GET | `/api/v1/platform/me` | Current platform grant | Bearer | `platform.access` | Read | Role/permission only | Identity | READY |
| Identity | GET | `/api/v1/platform/identities`, `/{id}` | Bounded account metadata/search | Bearer | `platform.identities.read` | Read | No hash, phone, tokens or OTP | Identity | READY |
| Identity | GET | `/api/v1/platform/sessions` | Bounded session metadata | Bearer | `platform.sessions.read` | Read | No refresh token/IP/user-agent | Identity | READY |
| Identity | GET | `/api/v1/platform/audit` | Operator grant audit | Bearer | `platform.audit.read` | Read | No secret payload | Identity | READY |
| Identity | GET | `/api/v1/platform/admins` | Active platform-grant identities | Bearer | `platform.audit.read` | Read | No hashes, tokens or phone values | Identity | READY |
| Organization | GET | `/api/v1/platform/organizations/`, `/{id}/` | Bounded organization structure | Bearer | `platform.organizations.read` | Read | No invitation tokens/private chat | Organization | READY |
| Gateway | GET | `/api/v1/platform/services` | Nine-service live/ready aggregate | Bearer | `platform.services.read` | Read | No config or credentials | Gateway | READY |
| Organization | GET | Tenant resource routes | Company structure; Django tenant queryset and capability checks | Bearer | Tenant only | Both | Tenant only | Organization | NOT APPROPRIATE |
| User | GET/PATCH | `/api/v1/users/*` | Own profile/workspace people | Bearer | Tenant only | Both | Privacy/block enforced | User | NOT APPROPRIATE |
| Conversation | All | `/api/v1/conversations/*` | Participant conversation lifecycle | Bearer | Tenant participant | Both | No generic platform contract | Conversation | NOT APPROPRIATE |
| Messaging | All | Messages/receipts routes | Participant message content and receipts | Bearer | Tenant participant | Both | Content must not become diagnostics | Messaging | NOT APPROPRIATE |
| Realtime | WS | `/api/v1/realtime` | Participant event transport | Bearer | Tenant participant | Both | No private stream/counters API | Realtime | NOT APPROPRIATE |
| Media | All | `/api/v1/media/*` | Authorized private media/signatures | Bearer | Tenant/uploader | Both | No content/signature browser | Media | NOT APPROPRIATE |
| Notification | All | `/api/v1/notifications/*` | Recipient preferences/tokens | Bearer | Tenant/recipient | Both | No provider/token inspection | Notification | NOT APPROPRIATE |

## Observed constraints

Organization uses DRF filtering/search/order/pagination and capability-specific mutations; tenant querysets are authoritative. FastAPI services use signed tenant/member context, explicit schemas, bounded pagination where present, and participant/recipient checks. Internal provisioning and block-check endpoints use service authentication and must not become browser APIs. Outbox repositories exist but no safe platform operational API exists. Existing Identity security audit is private application data, not a general credential/debug browser. New platform contracts must explicitly select safe fields, enforce persistent authorization on each request, and use separate namespaces.

## Current platform information architecture

Platform Administration uses explicit platform APIs only: Dashboard, Organizations and organization metadata, Users/Identities, Platform Administrators, Sessions, Service Health and Platform Audit. Organization tenant resources, private communications, media, notifications and invitation contents remain unavailable to platform administration until an explicit, privacy-reviewed contract exists.
