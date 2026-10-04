Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Private local media
MEDIA_STORAGE_BACKEND=local uses signed HMAC capabilities, bounded TTL <=900 seconds, tenant-scoped hashed object storage, durable metadata and outbox. Production still requires S3. No public directory or unsigned download route. Upload body bytes directly to upload_url with required_headers, then POST /media/{id}/complete; wait for Messaging ready projection, then send type IMAGE/VIDEO/AUDIO/VOICE/DOCUMENT with media_id. Recipient obtains authorized download_url. Local CORS permits localhost:3000.

Single PUT/part limit 64 MiB; larger files use existing multipart flow. Multipart parts are checked by number/etag, can resume and abort. Images <=10 MiB; supported documents PDF; other type limits follow actual policy. No arbitrary document formats invented.

YOU DO THIS MANUALLY: attach real image/video/audio/PDF in browser, cancel/retry an upload; play voice recording and revoke mic permissions; inspect signed recipient download and media viewer. Microphone and actual camera hardware require your permission and manual check.
