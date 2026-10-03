# Notification and settings source readiness

No deployment, AWS changes or push messages were performed.

Notification inbox is a bounded, authenticated read-only API scoped by organization, recipient member and recipient user. Existing records have no read flag or creation timestamp. The UI does not fabricate unread counts, timestamps or mark-read operations. Pagination uses stable record identity rather than invented chronology. Clicking opens the authorized conversation; individual historical-message navigation remains unavailable.

Preferences persist only push_enabled and notification_preview (mapped to preview). Separate group/sound controls accepted by the legacy request schema are not persisted by the API and therefore are not offered as working controls.

Browser permission is requested only following an explicit click while permission is default. Browser Firebase token acquisition, service worker delivery, registration and foreground push are unavailable pending a supported web delivery configuration. No tokens or credentials are collected.

Profile and privacy use existing User endpoints. Appearance is frontend-local with guarded storage access, system-theme listener cleanup and an early theme script. Account access remains administrator-controlled. Existing linked-device revocation/logout confirmation is preserved.

Production requirements still include Phase 4/5 migrations, summary backfill, updated application deployment and live S3/CORS verification. This gate validates source and automated tests, not live production behavior.
