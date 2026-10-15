"""Personal scope, read state, conversation mute, blocks, preference fields."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_personal_read_mute_blocks"
down_revision = "0005_delivery_recovery_fields"
branch_labels = depends_on = None


def upgrade():
    uuid = postgresql.UUID(as_uuid=True)
    for table in (
        "notifications",
        "notification_deliveries",
        "device_push_tokens",
        "outbox_events",
    ):
        op.alter_column(table, "organization_id", nullable=True)

    op.add_column(
        "notifications",
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.alter_column("notifications", "conversation_id", nullable=True)
    op.alter_column("notifications", "message_id", nullable=True)

    op.add_column(
        "notification_preferences",
        sa.Column("message_notifications", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("group_notifications", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("sound_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    )
    op.add_column(
        "notification_preferences",
        sa.Column("vibration_enabled", sa.Boolean(), server_default=sa.true(), nullable=False),
    )

    op.create_table(
        "conversation_mutes",
        sa.Column("id", uuid, primary_key=True),
        sa.Column("organization_id", uuid, nullable=True),
        sa.Column("conversation_id", uuid, nullable=False),
        sa.Column("user_id", uuid, nullable=False),
        sa.Column("member_id", uuid, nullable=False),
        sa.UniqueConstraint(
            "organization_id",
            "conversation_id",
            "member_id",
            name="uq_conversation_mute_member",
        ),
    )

    op.create_table(
        "user_block_projections",
        sa.Column("blocker_user_id", uuid, primary_key=True),
        sa.Column("blocked_user_id", uuid, primary_key=True),
    )


def downgrade():
    op.drop_table("user_block_projections")
    op.drop_table("conversation_mutes")
    for column in (
        "vibration_enabled",
        "sound_enabled",
        "group_notifications",
        "message_notifications",
    ):
        op.drop_column("notification_preferences", column)
    op.drop_column("notifications", "read_at")
    for table in (
        "notifications",
        "notification_deliveries",
        "device_push_tokens",
        "outbox_events",
    ):
        op.alter_column(table, "organization_id", nullable=False)
