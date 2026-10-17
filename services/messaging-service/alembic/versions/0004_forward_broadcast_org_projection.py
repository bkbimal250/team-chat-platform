"""Forward metadata, org member projection, personal broadcast lists."""

import sqlalchemy as sa
from alembic import op

revision = "0004_fwd_broadcast_org"
down_revision = "0003_personal_direct"
branch_labels = depends_on = None


def upgrade():
    # 0001 applies current metadata on a fresh database.
    inspector = sa.inspect(op.get_bind())
    message_columns = {column["name"] for column in inspector.get_columns("messages")}
    if "forward_from_message_id" not in message_columns:
        op.add_column(
            "messages",
            sa.Column("forward_from_message_id", sa.UUID(), nullable=True),
        )
    if "forward_from_conversation_id" not in message_columns:
        op.add_column(
            "messages",
            sa.Column("forward_from_conversation_id", sa.UUID(), nullable=True),
        )
    if inspector.has_table("organization_member_projections"):
        return
    op.create_table(
        "organization_member_projections",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("member_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.UniqueConstraint("organization_id", "member_id", name="org_member_projection_unique"),
    )
    op.create_table(
        "personal_broadcast_lists",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("owner_user_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("broadcast_list_owner", "personal_broadcast_lists", ["owner_user_id"])
    op.create_table(
        "personal_broadcast_recipients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("list_id", sa.UUID(), nullable=False),
        sa.Column("contact_id", sa.UUID(), nullable=False),
        sa.Column("recipient_identity_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["list_id"], ["personal_broadcast_lists.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("list_id", "recipient_identity_id", name="broadcast_recipient_unique"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("personal_broadcast_recipients")
    op.drop_index("broadcast_list_owner", table_name="personal_broadcast_lists")
    op.drop_table("personal_broadcast_lists")
    op.drop_table("organization_member_projections")
    op.drop_column("messages", "forward_from_conversation_id")
    op.drop_column("messages", "forward_from_message_id")
