"""Pending workspace invitation notifications for unlinked recipients."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0007_pending_invite_notif"
down_revision = "0006_personal_read_mute_blocks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pending_invitation_notifications",
        sa.Column("invitation_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recipient_phone_e164", sa.String(length=32), nullable=True),
        sa.Column("recipient_email", sa.String(length=320), nullable=True),
        sa.Column("fulfilled_user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_pending_invitation_phone",
        "pending_invitation_notifications",
        ["organization_id", "recipient_phone_e164"],
    )
    op.create_table(
        "identity_phone_projections",
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("phone_e164", sa.String(length=32), nullable=False),
    )
    op.create_index("ix_identity_phone_e164", "identity_phone_projections", ["phone_e164"])


def downgrade() -> None:
    op.drop_index("ix_identity_phone_e164", table_name="identity_phone_projections")
    op.drop_table("identity_phone_projections")
    op.drop_index("ix_pending_invitation_phone", table_name="pending_invitation_notifications")
    op.drop_table("pending_invitation_notifications")
