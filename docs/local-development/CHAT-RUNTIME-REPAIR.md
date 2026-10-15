# Local chat runtime repair — 2026-10-14

Changes:
- Contacts and notification fetches defer discarded Strict Mode setup and handle cancellation without error UI; cancelled chat list requests cannot overwrite newer results.
- Realtime connection setup is deferred, reconnect uses bounded backoff, online/offline listeners are cleaned up, and discarded sockets cannot update UI. Existing server session/device replacement semantics remain unchanged.
- Chat list searches titles and recent previews, with All/Unread/Groups filters; search supports clear and Escape. Conversation search explicitly covers loaded messages only.
- Personal New chat opens saved Contacts rather than workspace people. Mobile navigation is below the conversation instead of consuming its width.
- Notification migration 0008_personal_preferences allows personal settings with a partial unique identity index. Tenant uniqueness remains intact; repository uses the matching conflict target. Applied only to local development.
- Gateway preserves trailing slash when forwarding Django URLs, preventing redirect loops.
- Existing Messaging migration 0005_message_e2ee_envelope was checked/applied via local orchestration; no new Messaging migration or encryption policy changes.

Validation:
- Web full suite: 99 passed; lint, typecheck, production build passed.
- Notification: 58 passed, including personal preference uniqueness/isolation/rollback.
- Gateway: 72 passed, including GET/POST/PATCH trailing slash forwarding.
- Messaging: 81 passed after updating the existing fake Message fixture to include the current nullable envelope field.
- All nine local readiness endpoints returned HTTP 200.
- Personal notification preferences: repeated authenticated Gateway GET returned HTTP 200.
- Browser navigation Contacts -> Message passed at desktop and 390px mobile, no uncaught page errors. Screenshots verified and mobile layout corrected.

Limits of live verification:
- Extended browser send/search check was not completed: repeated test logins reached the existing rate limit. No limits cleared or weakened.
- Real API smoke reached messages/typing/receipts, attachment transport, reconnect, summaries and blocking checks; final organization fixture check returned 401. This is not a full end-to-end PASS. The earlier redirect loop is fixed.
- Attachment fixtures prove transport/authorization, not media codec playback.

No AWS/Terraform/production deployment, SMS or FCM was used.
