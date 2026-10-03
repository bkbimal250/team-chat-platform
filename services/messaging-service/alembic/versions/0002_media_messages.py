"""Durable media message references and authorized ready-media projection."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0002_media_messages"
down_revision = "0001_initial"
branch_labels = depends_on = None


def upgrade():
    bind = op.get_bind()
    if "attachment" not in {c["name"] for c in sa.inspect(bind).get_columns("messages")}:
        op.add_column("messages", sa.Column("attachment", JSONB(), nullable=True))
    if not sa.inspect(bind).has_table("media_projections"):
        op.create_table(
            "media_projections",
            sa.Column("id", UUID(as_uuid=True), primary_key=True),
            sa.Column("organization_id", UUID(as_uuid=True), nullable=False),
            sa.Column("conversation_id", UUID(as_uuid=True), nullable=False),
            sa.Column("uploader_member_id", UUID(as_uuid=True), nullable=False),
            sa.Column("status", sa.String(20), nullable=False),
            sa.Column("metadata_json", JSONB(), nullable=False),
        )
        op.create_index(
            "ix_media_projections_organization_id", "media_projections", ["organization_id"]
        )


def downgrade():
    op.drop_table("media_projections")
    op.drop_column("messages", "attachment")
