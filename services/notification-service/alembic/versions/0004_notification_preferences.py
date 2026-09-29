"""add tenant-scoped notification preference fields"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0004_notification_preferences"
down_revision = "0003_global_user_projection"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    existing_rows = bind.execute(sa.text("SELECT count(*) FROM notification_preferences")).scalar()
    if existing_rows:
        raise RuntimeError(
            "notification_preferences rows cannot be safely assigned tenant identities"
        )

    uuid = postgresql.UUID(as_uuid=True)
    op.add_column("notification_preferences", sa.Column("organization_id", uuid, nullable=True))
    op.add_column("notification_preferences", sa.Column("member_id", uuid, nullable=True))
    op.add_column(
        "notification_preferences",
        sa.Column("push_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("preview", sa.String(16), nullable=False, server_default="FULL"),
    )
    op.add_column(
        "notification_preferences",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.add_column(
        "notification_preferences",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )
    op.alter_column("notification_preferences", "organization_id", nullable=False)
    op.alter_column("notification_preferences", "member_id", nullable=False)
    op.create_unique_constraint(
        "uq_notification_preferences_tenant",
        "notification_preferences",
        ["organization_id", "member_id"],
    )


def downgrade():
    op.drop_constraint(
        "uq_notification_preferences_tenant", "notification_preferences", type_="unique"
    )
    for column in (
        "updated_at",
        "created_at",
        "preview",
        "push_enabled",
        "member_id",
        "organization_id",
    ):
        op.drop_column("notification_preferences", column)
