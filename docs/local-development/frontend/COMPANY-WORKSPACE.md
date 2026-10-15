# Company Workspace

Target: apps/web/web-chat-app. Chat remains at `/`; company registration is `/register`, login `/login`, employee acceptance `/join`.

Workspace routes: `/workspace`, `/workspace/members`, `/workspace/teams`, `/workspace/branches`, `/workspace/invitations`, `/workspace/company`, `/workspace/roles`, `/workspace/profile`, `/workspace/devices`, `/workspace/settings`.

The existing tested tenant resource components have been adapted locally into the `workspace/` namespace. They use the same web session and same-origin Gateway bridge; no third frontend or direct browser service calls. Organization roles/assignments are loaded after authoritative Identity context validation. No owner ID assumption or inferred platform access.

Owner/authorized management overview shows bounded real counts, recent members/activity and pending invitations. Member overview shows their actual teams/branches and permitted directories. Mutations use real APIs, validation, confirmation and refresh. Mobile resource tables become stacked labeled rows. Own-device, account/privacy/notification settings, theme, and existing chat/media/voice remain integrated.

Organization APIs require trailing slashes. Next automatic slash normalization is disabled so the Gateway receives the actual contract without a redirect loop.

Accepted gaps: email verification/recovery, disabled phone OTP, invitation email delivery and email-only regeneration, platform APIs, notification read-state/push. No unsupported success claims. Counts with more pages are explicitly bounded rather than fabricated totals.

## Validation

Web regression: 69 tests passed, zero failures. Lint/typecheck pass. Real local API/browser role matrix and all seven widths pass. Two-user direct conversation, messages, typing and reconnect pass. Workspace broadcasts remain unavailable; fallback refetch is implemented. Local fixtures were created through normal registration and invitation APIs; no OTP bypass or real SMS.

Final production build passes. Fresh local browser run: zero console/unhandled errors. A repeated stress run exhausted local PostgreSQL connections; restarting only Organization released its connections and readiness returned 200, with fresh registration/role checks passing again. Docker stayed running. Production configuration/code was not changed.
