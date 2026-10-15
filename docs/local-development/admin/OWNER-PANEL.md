# GlobalChat Owner/Admin workspace

The existing Next.js admin application at `apps/admin-web/admin-webchat-app` uses real Gateway APIs through its same-origin `/api/gateway` bridge. Start locally at http://localhost:3000/login. Email/password is primary; phone OTP remains disabled and preserved. Backend permissions, tenant ownership and invite-only employee onboarding remain authoritative.

Navigation groups: Overview, Organization, Communication, Access & Security, Account. Unsupported conversation moderation/security/system routes are retained as honest unavailable pages but removed from primary navigation. Company is the current authenticated organization, not a platform-wide organization directory.

The compact header follows the active page. Desktop navigation collapses; mobile navigation uses the shared accessible dialog with Escape, focus trapping and restoration. Tables scroll within their own region, not the whole page. Shared buttons, cards, status badges, error/retry states and dialogs are reused. Management operations remain pending until the server confirms them and then refetch authoritative data.

Dashboard shows bounded tenant member/branch/team/pending-invitation counts, authorized audit activity and pending invitations. A trailing plus means more than the first 50 records. No fabricated growth, online users, revenue or charts. Quick actions lead to the actual create flow on each management screen.

Members support server search/status/branch/team/role filters, cursor pagination, identity initials, current assignments, details, edit, role assignment, branch/team assignment and confirmed lifecycle operations under actual permissions. Only API-returned information is shown; employee email is not present in the member serializer. Invitation emails are available on Invitations.

Invitations use real email-bound recipients, role/branch/team IDs and status. Create/regenerate returns a development-only private link. Copy it privately; it is not stored in browser storage. Regenerate invalidates the old link and does not mean an email was sent. Revoke requires confirmation. Paid email delivery is unavailable.

Devices/Sessions apply to the current account only. Profile edits supported display name/about. Settings persist organization policy, user preferences/privacy and notification preferences to their real contracts. Chat appearance preference is persisted by User; the admin maintains its current accessible light color scheme.

See [routes](OWNER-PANEL-ROUTES.md), [refresh and realtime](OWNER-PANEL-REALTIME.md) and [manual checks](OWNER-PANEL-MANUAL-TESTING.md).

## Verified limitation

The current Organization resend endpoint requires a recipient phone. Email-only invitations can be created and revoked, but link regeneration is unavailable and is explicitly marked in the UI. No backend workaround or identity change was made.
