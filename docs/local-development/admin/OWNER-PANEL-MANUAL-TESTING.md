# Owner Panel manual verification

1. Open http://localhost:3000/login with a local Owner email/password. Register a disposable company only if needed at http://localhost:3000/register; no OTP/SMS.
2. At http://localhost:3000/dashboard inspect real bounded counts, pending invitations and activity. Quick actions open the existing management screens.
3. At http://localhost:3000/organizations edit supported company fields, save/cancel, open current-company tabs; unknown organization IDs must not expose another tenant.
4. At http://localhost:3000/branches create/edit a local branch and confirm before disabling it. Repeat create/edit for http://localhost:3000/teams.
5. At http://localhost:3000/members search and filter status/branch/team/role; inspect details and authorized assignments. Never remove a real colleague just to test.
6. At http://localhost:3000/invitations invite a disposable local employee email. Copy the private link. Regenerate/revoke are real operations and old links stop working.
7. In a separate browser open that returned http://localhost:3001/join#invite=… link, set the invited employee password and enter web chat. Keep Admin Members open: acceptance appears at the next active 30-second API refresh. Check Invitations becomes Accepted and Dashboard counts change. There is no public member-event broadcast.
8. Check http://localhost:3000/profile, http://localhost:3000/settings and http://localhost:3000/devices. Settings save to real APIs; devices/sessions are your own only.
9. Test 1440/1366/1280/1024/768/430/390 widths; mobile drawer, Escape, Tab focus trap, tables and dialogs. Use normal in-app links rather than repeatedly hard-reloading pages and exhausting backend read throttles.
10. Go offline then online: state recovers via authoritative refetch. Logout via the account menu; protected content disappears and a normal employee cannot enter admin.

Accepted gaps: email verification/recovery, legacy OTP password setup, invitation email delivery, cross-user device administration, notification read-state, conversation moderation and admin membership push events.

## Verified limitation

The current Organization resend endpoint requires a recipient phone. Email-only invitations can be created and revoked, but link regeneration is unavailable and is explicitly marked in the UI. No backend workaround or identity change was made.
