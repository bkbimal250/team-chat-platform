Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Known gaps
1. Notification mark-read/unread browser push contracts remain intentionally unavailable; inbox/preferences supported. Local push provider is explicit simulation; no real FCM sent.
2. Browser hardware camera/microphone, file playback/viewer, offline/mobile/two-browser checks require manual confirmation. Automated API/media byte checks do not prove hardware capture or browser playback.
3. Some consumer poison-message failures requeue indefinitely; no universal DLQ/retry policy. Existing architecture retained.
4. npm ci reported dependency advisories; inspect npm audit before a future production release. No force upgrade performed.
5. Local storage mimics private signed transfer but does not verify production S3/CORS. AWS infrastructure remains decommissioned.
6. Platform administration C1 deliberately does not expose cross-tenant User profiles, conversation/message/media content, realtime counters, notification diagnostics, or cross-user session/device actions. Each needs an explicit privacy-reviewed platform contract before C2 uses it.
# Current verification limits — 2026-10-05

Local APIs were unreachable during documentation verification and PostgreSQL connections timed out. Full live mutation, broker, browser and database tests must be rerun after local infrastructure and services are started. No OTP, provider, media upload, seed or migration was executed for this documentation task.

QR cancellation/rejection is not a current endpoint. Notification inbox has no unread/read-state mutations; browser push and invitation delivery capabilities must be checked against their existing provider configuration rather than assumed from UI. Platform-wide organization administration, cross-user device administration and conversation moderation are not supplied by the current tenant API.
