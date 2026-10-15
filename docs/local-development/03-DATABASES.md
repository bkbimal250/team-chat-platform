Last verified: 2026-10-04. Scope: existing GlobalChat local development only.

# Database ownership and migrations
Separate PostgreSQL databases: teamchat_organization_db, identity_db, teamchat_user_db, conversation_db, teamchat_message_db, teamchat_media_db, teamchat_notification_db. Local role postgres; generated local password. No Realtime/Gateway database.

`python scripts/local/dev.py migrate` creates missing names only and runs real migrations sequentially. Logs/current revisions: .local/*-migration*.log. Organization Django includes 0002_tenant_integrity and later onboarding migrations; consult `manage.py showmigrations` for every app. Current Alembic source heads: Identity 0005_email_password; User 0002_outbox_delivery_state; Conversation 0002_chat_summaries; Messaging 0002_media_messages; Media 0002_usage_reserved_bytes; Notification 0005_delivery_recovery_fields. Source heads are not proof of the applied physical database revision. Use `alembic current` in the owning service's configured environment to verify it; do not execute migrations as a documentation check.

Tests use separate test_ prefixed databases; Django creates its isolated test database. No production migrations or database resets. Historical summary backfill if importing old local history: run Messaging module `app.conversation_summary_rebuild` through the local environment; it stages idempotent summary events consumed by Conversation. Fresh seed has no historical import to backfill.
