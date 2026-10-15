"""Nullable personal scope with non-null conversation/actor uniqueness."""

import sqlalchemy as sa

from alembic import op

revision = "0003_personal_direct"
down_revision = "0002_media_messages"
branch_labels = depends_on = None
TABLES = (
    "conversation_projections",
    "conversation_member_projections",
    "messages",
    "media_projections",
    "message_reactions",
    "conversation_read_states",
    "outbox_events",
)


def upgrade():
    for table in TABLES:
        op.alter_column(table, "organization_id", nullable=True)
    op.create_index(
        "personal_message_idempotency",
        "messages",
        ["conversation_id", "sender_device_id", "client_message_id"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NULL"),
    )
    op.create_index(
        "personal_read_state_unique",
        "conversation_read_states",
        ["conversation_id", "member_id"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NULL"),
    )


def downgrade():
    for table in TABLES:
        op.alter_column(table, "organization_id", nullable=False)
    op.drop_index("personal_message_idempotency", table_name="messages")
    op.drop_index("personal_read_state_unique", table_name="conversation_read_states")
