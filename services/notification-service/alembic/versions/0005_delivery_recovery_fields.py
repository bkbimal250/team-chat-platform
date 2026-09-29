"""add durable delivery recovery fields"""

import sqlalchemy as sa

from alembic import op

revision = "0005_delivery_recovery_fields"
down_revision = "0004_notification_preferences"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("notification_deliveries", sa.Column("last_error", sa.String(512), nullable=True))
    op.add_column(
        "notification_deliveries",
        sa.Column("claimed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade():
    op.drop_column("notification_deliveries", "claimed_at")
    op.drop_column("notification_deliveries", "last_error")
