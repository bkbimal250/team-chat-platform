# Media messages rollout

Source implementation only: no production deployment, upload or migration was performed.

Apply `0002_media_messages` before starting the updated Messaging API/consumer. The migration adds nullable message attachment metadata and durable ready-media projections; existing text messages remain valid.

Deploy the updated Media service/publisher so `media.ready.v1`, `media.deleted.v1` and `media.failed.v1` include uploader/conversation and safe file metadata. The Messaging consumer binds these events on `media.events`. Media tombstones prevent late ready events from reviving deleted files. Legacy ready events without ownership metadata never authorize a send.

Media verifies the authenticated caller against the existing Conversation detail API on every operation. `CONVERSATION_API_URL` defaults to the same private Cloud Map endpoint already used by Gateway. Redirects are rejected, timeouts are bounded, and the token is neither logged nor sent to S3. Participants may download; only the uploader may finalize/abort/delete.

Frontend uploads bytes directly to signed S3 URLs, including sequential multipart parts. Existing S3 CORS must permit the frontend origin and PUT and expose ETag for multipart uploads; no bucket/CORS changes were made in this task.

A completed upload can briefly return MEDIA_NOT_READY from Messaging while the ready event is delivered. Retry reuses its confirmed media ID and client message id. Only confirmed Messaging responses appear as sent. Failed multipart uploads are aborted; simple upload orphans retain existing cleanup behavior.

Browser voice recording requires a secure context and an allowed MediaRecorder format (WebM or Ogg). Unsupported formats are reported explicitly. No recording uploads before Send.
