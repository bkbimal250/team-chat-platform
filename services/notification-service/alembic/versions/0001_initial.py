import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_push_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("member_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("platform", sa.String(16), nullable=False),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.UniqueConstraint("organization_id", "device_id", name="uq_push_device"),
    )
    for name in (
        "notification_preferences",
        "notifications",
        "notification_deliveries",
        "processed_events",
        "outbox_events",
    ):
        op.create_table(name, sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True))


def downgrade():
    for name in (
        "outbox_events",
        "processed_events",
        "notification_deliveries",
        "notifications",
        "notification_preferences",
        "device_push_tokens",
    ):
        op.drop_table(name)
