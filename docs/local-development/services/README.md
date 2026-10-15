# Backend service API references

These references come from imported schemas and actual handlers, authentication dependencies, permission checks, models, migrations, events and tests. Internal provisioning, signed local-storage, WebSocket and Gateway forwarding operations excluded from OpenAPI are included. Implicit HEAD/OPTIONS are framework protocol handling.

- [Organization](ORGANIZATION-API.md)
- [Identity](IDENTITY-API.md)
- [User](USER-API.md)
- [Conversation](CONVERSATION-API.md)
- [Messaging](MESSAGING-API.md)
- [Realtime](REALTIME-API.md)
- [Media](MEDIA-API.md)
- [Notification](NOTIFICATION-API.md)
- [Gateway](GATEWAY-API.md)

[Actual local ports](../architecture/SERVICE-PORTS.md) · [Manual testing order](../manual-testing/README.md).

Read each endpoint's body constraints and source-backed response before sending. Empty response schemas mean no declared response model; they do not mean an empty response. Templates contain placeholders and must not be run wholesale. No real SMS, email or FCM was sent by this documentation task.
