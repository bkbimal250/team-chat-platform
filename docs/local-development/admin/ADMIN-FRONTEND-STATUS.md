# Owner Panel product phase — 2026-10-05

Responsive shell/navigation, real dashboard actions, member filters/assignments, private invitation copy/regeneration, own profile and personal settings/privacy are implemented. Admin membership push events are unavailable; scoped API polling/focus/reconnect keeps durable state authoritative. No backend modifications. See [product guide](OWNER-PANEL.md) and [refresh contract](OWNER-PANEL-REALTIME.md).

# Email/password verification — 2026-10-05



Current authentication results supersede the historical records below. Email/password is primary; phone OTP is disabled locally and its implementations remain preserved. Identity migration `0005_email_password` applied to local PostgreSQL. All nine API live/ready checks passed, and admin/web chat are running on ports 3000/3001.



Affected backend regression: Organization 74, Identity 121, User 39, Gateway 33: **267 passed, 0 failed, 0 skipped**. Admin: **36 passed**. Web chat: **50 passed**. Both frontends passed lint, typecheck and production builds.



Live Gateway checks passed company registration, Owner profile/membership/session, returning login, refresh/logout, email-bound employee invitation/password setup, employee profile/login and invitation replay rejection. Browser checks passed company registration, returning Owner login, invitation creation, employee web-chat onboarding and normal-member admin rejection. No OTP challenge was created and no SMS was sent.



Email verification and password reset are not implemented. Existing OTP-only accounts require a legitimate password setup/recovery flow. Invitation email delivery is not configured; local development uses a private invitation link. See [authentication policy](../onboarding/EMAIL-PASSWORD-AUTH.md).



## Owner Panel validation

Admin: **54 collected, 54 passed, 0 failed**. Lint/typecheck/production build pass. Browser: all requested widths (1440, 1366, 1280, 1024, 768, 430, 390) and all owner screens passed; zero React hydration/unhandled errors in the successful browser run; subsequent expired-session/throttled-fixture checks returned HTTP 401/429, zero direct-service HTTP calls, socket connected, offline indicator, authoritative reconnect refetch and no repeated request loop. Branch/team creation and invitation creation passed against real local APIs.

The two-browser employee acceptance retest was blocked by the existing local registration rate limit; counters were not cleared or weakened. The previous green email/password onboarding baseline remains preserved. Current email-only invitation regeneration is rejected by Organization and is marked unavailable; phone-bound regeneration is retained. Admin membership push events are unavailable; polling/focus/reconnect supplies honest API reconciliation.

## Historical records



# Admin real-API baseline



Verified locally on 2026-10-04. No AWS, Terraform, backend or production deployment changes were made for this integration.



## Screens and contracts



| Screen | Status | Actual behavior |

|---|---|---|

| Login/session | Real API | Development OTP, verification, rotating refresh, logout and permission guard |

| Dashboard | Partial | Real tenant resource counts (bounded pages explicitly qualified), recent audit; no invented global statistics |

| Organizations | Partial | Current organization only; view/update/settings. Global organization discovery and creation unavailable |

| Branches/Teams | Real API | Tenant-scoped lists, search, filters, cursors, forms and lifecycle confirmations |

| Members | Real API | Tenant membership create/update, lifecycle and role assignment. Creating a member does not create an Identity user |

| Invitations | Real API (local) | Phone-bound recipients, real role/branch/team assignments, development link, rotating resend and revoke |

| Roles/Audit | Real API | Current tenant role permissions/assignments and audit records |

| Devices/Sessions | Partial | Authenticated user's devices/sessions and revocation; no cross-user administrative endpoint |

| Notifications | Partial | Real own notification list; unread/read actions unavailable |

| Settings | Partial | Organization flags/timezone and push/preview preferences; unsupported settings labelled |

| Conversations/System/Security | Unavailable | No invented administrative contracts or persistence |



## Architecture and security



All requests use the existing Gateway via a same-origin Next route handler. Internal cursor URLs are reduced to their API path; private redirects are rejected. No direct-service browser requests. API authorization remains backend-authoritative. Roles are derived from actual current-member assignments and permissions. Session tokens are held in memory/per-tab sessionStorage, not printed. A failed refresh clears the session; a resource 403 does not falsely log the user out. Mutation errors and confirmations remain visible. No production mock records or invented capabilities are used; test doubles remain inside tests.



## Verification



20 unit/component tests pass, covering API errors/refresh, login, permission guards, resource rendering, forms and confirmations. The local browser/API runner executed 42 passing assertions: real development OTP login, expired token rejection and rotation, tenant lists, organization update, branch create/edit/disable/activate, unlinked member/team creation, invitation create/revoke, settings, own devices/sessions/notifications, logout, normal-user rejection and foreign-tenant/device access rejection. No browser exceptions. Results and screenshot are in ignored `.local/admin-live-results.json` and `.local/admin-dashboard.png`; no tokens or OTP values are included in the report.



Run `npm run test`, `npm run lint`, `npm run typecheck`, `npm run build`. Live checks are local-only (`npm run test:live`) and intentionally create/update isolated development fixtures; never use against production. Prepare foreign-tenant fixtures using `scripts/prepare-live-fixtures.py` through the local Organization runtime. Preserve OTP cooldown/rate limits.



## Accepted gaps



No platform-wide organization administration, global analytics, cross-user device administration, notification read state, or administrative conversation moderation contracts exist. Paid production invitation delivery remains future work. Main web now has real local employee onboarding; mobile is unchanged.





## Final company onboarding verification (2026-10-04)



Full backend: 401 collected / 401 passed / 0 failed / 0 skipped. Admin: 24 collected / 24 passed / 0 failed. Lint, TypeScript and production build pass. Actual local browser/API onboarding: 20 passed / 0 failed; three physical service-owned DB checks pass. Identity migration reaches single head `0003_company_registration`; repeat upgrade succeeds. `/register` is active, returning LOGIN OTP restores the same organization/membership/profile, and existing admin permission tests remain green. No real SMS/FCM, AWS changes or production deployment.





## Secure employee onboarding (2026-10-05)



Secure local employee invitation/OTP onboarding now replaces the previous missing-recipient/delivery gap. Invite/list/status/resend/revoke and accepted member assignment visibility use real APIs. Development delivery is explicitly local-only; paid production delivery remains unimplemented. Main web /join is connected.





## Final local verification â€” 2026-10-05



- Backend: 472 passed, 0 failed, 0 skipped (Organization 72, Identity 108, User 39, Conversation 20, Messaging 71, Media 47, Notification 50, Realtime 35, Gateway 30).

- Admin: 30 passed; web chat: 47 passed. Both lint, typecheck and production build pass.

- Real local browser/API/Rabbit workflow: 53/53 assertions pass. Physical PostgreSQL persistence: 12/12 assertions pass.

- Organization invitations `0002_recipient_onboarding` and Identity `0004_invitation_onboarding` applied locally; repeat migration succeeds.

- Existing-identity reuse, role/tenant boundaries, parallel acceptance, outbox rollback and bounded interrupted-provisioning recovery have executable regression coverage.

- No AWS/Terraform/production changes; no real SMS, email or FCM.

