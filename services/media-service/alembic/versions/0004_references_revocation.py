"""Reference conversation scope and revoked org members."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0004_references_revocation"
down_revision = "0003_personal_direct"
branch_labels = depends_on = None


def upgrade():
    op.add_column(
        "media_references",
        sa.Column("conversation_id", UUID(as_uuid=True), nullable=True),
    )
    op.create_index("ix_media_references_conversation_id", "media_references", ["conversation_id"])
    op.create_table(
        "revoked_org_members",
        sa.Column("organization_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("member_id", UUID(as_uuid=True), primary_key=True),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column(
            "revoked_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )


def downgrade():
    op.drop_table("revoked_org_members")
    op.drop_index("ix_media_references_conversation_id", table_name="media_references")
    op.drop_column("media_references", "conversation_id")
