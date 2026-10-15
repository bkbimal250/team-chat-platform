"""Allow isolated personal preferences and enforce one row per identity."""

import sqlalchemy as sa

from alembic import op

revision = "0008_personal_preferences"
down_revision = "0007_pending_invite_notif"
branch_labels = depends_on = None


def upgrade():
    op.alter_column("notification_preferences", "organization_id", nullable=True)
    op.create_index(
        "uq_notification_preferences_personal",
        "notification_preferences",
        ["member_id"],
        unique=True,
        postgresql_where=sa.text("organization_id IS NULL"),
    )


def downgrade():
    # Refuse to discard personal settings when returning to a tenant-only schema.
    count = (
        op.get_bind()
        .execute(
            sa.text("SELECT count(*) FROM notification_preferences WHERE organization_id IS NULL")
        )
        .scalar_one()
    )
    if count:
        raise RuntimeError("Cannot downgrade while personal preferences exist")
    op.drop_index("uq_notification_preferences_personal", table_name="notification_preferences")
    op.alter_column("notification_preferences", "organization_id", nullable=False)
