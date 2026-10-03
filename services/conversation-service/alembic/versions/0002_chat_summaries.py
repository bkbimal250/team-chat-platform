"""Durable conversation message/read projections; isolated schema additions."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0002_chat_summaries"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    # Legacy 0001 create_all can already create these on a fresh install.
    if not sa.inspect(bind).has_table("conversation_message_projections"):
        op.create_table(
            "conversation_message_projections",
            sa.Column("message_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
            sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
            sa.Column("sender_member_id", UUID(as_uuid=True), nullable=False),
            sa.Column("sequence", sa.BigInteger(), nullable=False),
            sa.Column("preview", sa.String(200), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("version_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("is_deleted", sa.Boolean(), nullable=False),
        )
        op.create_index(
            "conversation_message_summary",
            "conversation_message_projections",
            ["organization_id", "conversation_id", "sequence"],
        )
    if not sa.inspect(bind).has_table("conversation_read_projections"):
        op.create_table(
            "conversation_read_projections",
            sa.Column("organization_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("conversation_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("member_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("sequence", sa.BigInteger(), nullable=False),
        )


def downgrade():
    op.drop_table("conversation_read_projections")
    op.drop_index("conversation_message_summary", table_name="conversation_message_projections")
    op.drop_table("conversation_message_projections")
