# Owner Panel realtime and authoritative refresh

## Actual server contract

Source inspected: `services/realtime-service/app/main.py`, `events.py`, `registry.py`. Endpoint `/api/v1/realtime` authenticates a token, supports version 1 ping/pong and authorized conversation subscriptions/typing. Delivered message frames have `{version:1,type:"message.created.v1",payload:{...}}` and analogous message updates/reactions/receipts. Conversation lifecycle events invalidate subscriptions; they are not admin organization broadcasts.

**Member, branch, team, invitation and device administrative WebSocket events are UNAVAILABLE.** RabbitMQ membership events existing internally do not prove public WebSocket delivery. No invented event names or subscriptions are sent. The admin does not subscribe to or expose employee conversations.

| Event / trigger | Source | Screen | UI effect | Reconnect | Fallback |
|---|---|---|---|---|---|
| ping/pong version 1 | Realtime WebSocket | Connection indicator | Subtle connecting/reconnecting/offline state; no business mutation | Bounded exponential backoff 1–30 seconds, fresh current token | HTTP remains authoritative |
| Successful admin mutation | Actual Gateway response | Affected resource, dashboard/audit | Scoped API invalidation | Refetch | Manual refresh |
| Realtime reconnect | Actual socket lifecycle | Mounted managed lists | Refetch authoritative API rows | Always refetch after reopening | Online/focus/visibility reconciliation |
| Visible-window 30-second interval | Local scheduler | Mounted members/invitations/dashboard/branches/teams/devices/notifications/company | Refetch authoritative scoped data | No dependency on receiving events | Pauses fetch while hidden/offline |
| Browser focus / online / visible | Browser lifecycle | Mounted managed resources | Catch up missed changes through APIs | Reconnect with current session | Manual retry |

Wrong-tenant scoped invalidations are ignored by matching the active authenticated session's organization. Arbitrary, duplicate or unscoped WebSocket frames never mutate admin data. AbortController discards superseded HTTP responses. Logout/unmount removes sockets, timers and event listeners. No token, invitation capability or frame payload is logged.

Employee acceptance becomes visible within the next active polling interval or focus/refetch. This is **API polling**, not push membership updates. The UI never claims otherwise. Accepted invitations and dashboard metrics are reconstructed from durable backend APIs.

Configure `NEXT_PUBLIC_REALTIME_URL` with the existing realtime origin (local port 8007); it is a public endpoint configuration, not a credential. No endpoint set means HTTP fallback still works without a misleading connection indicator.

## Verified limitation

The current Organization resend endpoint requires a recipient phone. Email-only invitations can be created and revoked, but link regeneration is unavailable and is explicitly marked in the UI. No backend workaround or identity change was made.
