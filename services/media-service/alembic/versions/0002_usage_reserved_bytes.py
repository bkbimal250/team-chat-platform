"""persist multipart reserved-byte accounting

Revision ID: 0002_usage_reserved_bytes
Revises: 0001_media_schema
"""

import sqlalchemy as sa

from alembic import op

revision = "0002_usage_reserved_bytes"
down_revision = "0001_media_schema"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organization_storage_usage",
        sa.Column("reserved_bytes", sa.BigInteger(), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("organization_storage_usage", "reserved_bytes")
