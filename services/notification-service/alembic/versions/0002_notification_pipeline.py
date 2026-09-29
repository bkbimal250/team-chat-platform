"""extend notification base tables with pipeline schema"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0002_notification_pipeline"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def add(table, *columns):
    for column in columns:
        op.add_column(table, column)


def upgrade():
    uuid = postgresql.UUID(as_uuid=True)
    add(
        "notifications",
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("conversation_id", uuid, nullable=False),
        sa.Column("message_id", uuid, nullable=False),
        sa.Column("recipient_user_id", uuid, nullable=False),
        sa.Column("recipient_member_id", uuid, nullable=False),
        sa.Column("notification_type", sa.String(32), nullable=False),
        sa.Column("title", sa.String(255)),
        sa.Column("body", sa.Text()),
        sa.Column("preview_mode", sa.String(16), nullable=False),
    )
    op.create_unique_constraint(
        "uq_notification_message_recipient",
        "notifications",
        ["organization_id", "message_id", "recipient_member_id", "notification_type"],
    )
    op.create_index(
        "ix_notifications_lookup", "notifications", ["organization_id", "conversation_id"]
    )
    add(
        "notification_deliveries",
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("notification_id", uuid, nullable=False),
        sa.Column("device_push_token_id", uuid, nullable=False),
        sa.Column("device_id", uuid, nullable=False),
        sa.Column("provider", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True)),
    )
    op.create_unique_constraint(
        "uq_delivery_notification_token",
        "notification_deliveries",
        ["notification_id", "device_push_token_id"],
    )
    op.create_index(
        "ix_notification_deliveries_lookup",
        "notification_deliveries",
        ["organization_id", "status", "next_attempt_at"],
    )
    add(
        "processed_events",
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("organization_id", uuid),
    )
    op.create_unique_constraint("uq_processed_event", "processed_events", ["event_id"])
    add(
        "outbox_events",
        sa.Column("event_id", uuid, nullable=False),
        sa.Column("event_type", sa.String(128), nullable=False),
        sa.Column("organization_id", uuid, nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
    )
    op.create_unique_constraint("uq_outbox_event", "outbox_events", ["event_id"])
    op.create_index("ix_outbox_events_lookup", "outbox_events", ["status"])
    for name, columns, unique in (
        ("user_projections", ("user_id", "display_name", "status"), ("organization_id", "user_id")),
        (
            "membership_projections",
            ("member_id", "user_id", "status"),
            ("organization_id", "member_id"),
        ),
        (
            "conversation_projections",
            ("conversation_id", "conversation_type", "status"),
            ("organization_id", "conversation_id"),
        ),
        (
            "conversation_member_projections",
            ("conversation_id", "member_id", "user_id", "status"),
            ("organization_id", "conversation_id", "member_id"),
        ),
    ):
        op.create_table(
            name,
            sa.Column("id", uuid, primary_key=True),
            sa.Column("organization_id", uuid, nullable=False),
            *[
                sa.Column(column, uuid if column.endswith("id") else sa.String(255), nullable=False)
                for column in columns
            ],
            sa.UniqueConstraint(*unique, name=f"uq_{name}_tenant"),
        )
    op.create_index(
        "ix_conversation_member_projections_lookup",
        "conversation_member_projections",
        ["organization_id", "conversation_id"],
    )


def downgrade():
    op.drop_index(
        "ix_conversation_member_projections_lookup", table_name="conversation_member_projections"
    )
    for name in (
        "conversation_member_projections",
        "conversation_projections",
        "membership_projections",
        "user_projections",
    ):
        op.drop_table(name)
    op.drop_index("ix_outbox_events_lookup", table_name="outbox_events")
    op.drop_constraint("uq_outbox_event", "outbox_events", type_="unique")
    for column in ("status", "payload", "organization_id", "event_type", "event_id"):
        op.drop_column("outbox_events", column)
    op.drop_index("ix_notification_deliveries_lookup", table_name="notification_deliveries")
    op.drop_constraint("uq_delivery_notification_token", "notification_deliveries", type_="unique")
    for column in (
        "next_attempt_at",
        "attempt_count",
        "status",
        "provider",
        "device_id",
        "device_push_token_id",
        "notification_id",
        "organization_id",
    ):
        op.drop_column("notification_deliveries", column)
    op.drop_index("ix_notifications_lookup", table_name="notifications")
    op.drop_constraint("uq_notification_message_recipient", "notifications", type_="unique")
    for column in (
        "preview_mode",
        "body",
        "title",
        "notification_type",
        "recipient_member_id",
        "recipient_user_id",
        "message_id",
        "conversation_id",
        "organization_id",
    ):
        op.drop_column("notifications", column)
    op.drop_constraint("uq_processed_event", "processed_events", type_="unique")
    for column in ("organization_id", "event_type", "event_id"):
        op.drop_column("processed_events", column)
