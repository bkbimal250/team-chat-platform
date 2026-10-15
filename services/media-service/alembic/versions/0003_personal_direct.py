"""Personal media scope and separately accounted private storage."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision = "0003_personal_direct"
down_revision = "0002_usage_reserved_bytes"
branch_labels = depends_on = None


def upgrade():
    for table in ("media", "outbox_events"):
        op.alter_column(table, "organization_id", nullable=True)
    if not sa.inspect(op.get_bind()).has_table("personal_storage_usage"):
        op.create_table(
            "personal_storage_usage",
            sa.Column("identity_id", UUID(as_uuid=True), primary_key=True),
            sa.Column("stored_bytes", sa.BigInteger(), nullable=False),
            sa.Column("media_count", sa.Integer(), nullable=False),
            sa.Column("reserved_bytes", sa.BigInteger(), nullable=False),
        )


def downgrade():
    for table in ("media", "outbox_events"):
        op.alter_column(table, "organization_id", nullable=False)
    op.drop_table("personal_storage_usage")
