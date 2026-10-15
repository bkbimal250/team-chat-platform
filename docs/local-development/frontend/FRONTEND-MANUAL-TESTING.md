# Frontend manual testing

1. Company owner: http://localhost:3001/register then http://localhost:3001/workspace. Open Members, invite using a real role, copy the locally returned private link. Email delivery is unavailable.
2. Employee: open the copied http://localhost:3001/join link in a separate browser; complete email/password acceptance. Visit http://localhost:3001/workspace/members: permitted directory only, no invitation/remove/role actions. Direct http://localhost:3001/workspace/invitations must show denial.
3. Second owner: use an owner-authorized invitation/role assignment. Verify management permissions independently; never assume a single permanent owner.
4. Chat: http://localhost:3001/. Owner/member open a direct conversation, exchange text, check typing/read state, disconnect/reconnect. Test media/voice using supported local storage configuration.
5. Appearance: http://localhost:3001/workspace/settings; select Light/Dark/System. Check 1440, 1366, 1280, 1024, 768, 430 and 390 widths, keyboard navigation, mobile drawer and dialog Escape.
6. Other tenant: use separate authorized company identity; resources outside that tenant must fail in the backend.

Local automated browser/API checks: four roles, all workspace screens and seven widths, second owner management, member mutation denial, cross-tenant 404, two-user messages/typing/reconnect. No paid OTP/SMS or AWS operations.

Workspace member/invitation broadcast events are absent: visible-online polling every 30 seconds, focus/online refresh and mutation invalidation are explicit fallback. Chat WebSocket reconnect also invalidates authoritative workspace resources. No invented events or fake presence.
