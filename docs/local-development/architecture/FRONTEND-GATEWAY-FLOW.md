# Frontend → Gateway → service

The admin application on port 3000 calls its Next.js `/api/gateway/[...path]` bridge. The bridge removes `/api/gateway` and forwards the original API path to the configured Gateway. `NEXT_PUBLIC_API_BASE_URL` is the admin configuration; the main web application uses `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_WS_URL`. Use Gateway port 8008 and Realtime port 8007 locally. Main web can use port 3001 alongside admin.

| Public namespace | Owner |
|---|---|
| `/api/v1/auth/**`, `/api/v1/devices/**` | Identity |
| `/api/v1/users/**` | User |
| Organization, branch, team, member, invitation, role, permission, role-assignment and audit resources | Organization |
| Conversation message/delivered/read subresources; `/api/v1/messages/**` | Messaging |
| Remaining `/api/v1/conversations/**` | Conversation |
| `/api/v1/media/**` | Media |
| `/api/v1/notifications/**` | Notification |

Messaging-specific matches precede the Conversation catch-all. Gateway forwards Authorization and the original protocol; downstream services enforce JWT, tenant and membership rules. Internal provisioning/authorization routes are direct server-to-server calls, never browser Gateway routes. See [the actual routing implementation](../../../services/gateway-service/app/routing.py) and [complete Gateway reference](../services/GATEWAY-API.md).

WebSocket connections go directly to Realtime, not the HTTP Gateway. Media metadata/signing goes through Gateway, while bytes use the returned signed storage URL. Local signed storage paths are documented in [Media](../services/MEDIA-API.md); production presigned S3 URLs are not fabricated locally.

For an upstream-unavailable error, check the owning service's readiness before retrying a mutation. Gateway readiness alone does not prove all upstreams are available. OTP requests can send paid SMS when the private Identity configuration uses Vonage; never retry automatically.
