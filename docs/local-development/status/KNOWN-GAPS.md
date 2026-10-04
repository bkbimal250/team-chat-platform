Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Known gaps
1. Notification mark-read/unread browser push contracts remain intentionally unavailable; inbox/preferences supported. Local push provider is explicit simulation; no real FCM sent.
2. Browser hardware camera/microphone, file playback/viewer, offline/mobile/two-browser checks require manual confirmation. Automated API/media byte checks do not prove hardware capture or browser playback.
3. Some consumer poison-message failures requeue indefinitely; no universal DLQ/retry policy. Existing architecture retained.
4. npm ci reported dependency advisories; inspect npm audit before a future production release. No force upgrade performed.
5. Local storage mimics private signed transfer but does not verify production S3/CORS. AWS infrastructure remains decommissioned.
