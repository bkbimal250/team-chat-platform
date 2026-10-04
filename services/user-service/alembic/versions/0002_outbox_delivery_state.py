"""Persist fields already required by the User transactional publisher."""

import sqlalchemy as sa

from alembic import op

revision = "0002_outbox_delivery_state"
down_revision = "0001_initial"
branch_labels = depends_on = None


def upgrade():
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("outbox_events")}
    columns = [
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.String(256), nullable=True),
    ]
    for column in columns:
        if column.name not in existing:
            op.add_column("outbox_events", column)


def downgrade():
    for name in ["last_error", "retry_count", "published_at", "created_at"]:
        op.drop_column("outbox_events", name)
