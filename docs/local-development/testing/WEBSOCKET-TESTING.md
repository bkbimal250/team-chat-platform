Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# WebSocket testing
URL ws://localhost:8007/api/v1/realtime?token=<ACCESS_TOKEN>. Tokens must remain private. Client frame examples:
```json
{"version":1,"type":"subscribe","conversation_id":"<ID>"}
{"version":1,"type":"typing.start","conversation_id":"<ID>"}
{"version":1,"type":"typing.stop","conversation_id":"<ID>"}
{"version":1,"type":"presence.heartbeat"}
```
Expected subscribe.ok; typing.updated.v1 sent to other authorized subscribed members. Typing expires after five seconds. Server message.created/edited/deleted/reaction_added/reaction_removed/delivered/read.v1 events carry payload. Authorization is checked through actual Conversation internal endpoint; unauthorized tokens/subscriptions close with 1008. No client-side message creation over WebSocket; send through Messaging HTTP API. YOU DO THIS MANUALLY: use two Postman WebSocket tabs with each user's token; subscribe both; HTTP send; inspect recipient frame. Reconnect and resubscribe. Never include query tokens in screenshots.
