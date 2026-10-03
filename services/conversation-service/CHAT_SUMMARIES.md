# Conversation summaries rollout

This change is source-only. No production migration or backfill has been executed.

1. Apply Conversation Service migration `0002_chat_summaries` using its existing migration process.
2. Start the updated Conversation consumer so its Messaging event bindings are active.
3. Start the updated Messaging publisher/API and Conversation API.
4. For existing message history, explicitly run `python -m app.conversation_summary_rebuild --stage` in Messaging Service after deployment approval. The existing outbox publisher delivers these snapshot events.

The rebuild stages only `conversation.summary.message.v1` and `conversation.summary.read.v1`, not ordinary message-created events. It does not replay notifications. Snapshots preserve message version timestamps and monotonic read watermarks, so late snapshots cannot replace newer state. Repeating the rebuild converges without duplicating summary rows.

Until historical snapshots arrive, pre-existing conversations have empty summaries. New message/read events populate durable tenant-scoped projections. The list API uses two batched summary queries and requires the existing authenticated membership.
