"""Personal direct conversation scope, explicit participant identity and uniqueness."""

import sqlalchemy as sa

from alembic import op

revision = "0003_personal_direct"
down_revision = "0002_chat_summaries"
branch_labels = depends_on = None

TABLES = (
    "conversations",
    "conversation_members",
    "outbox_events",
    "conversation_message_projections",
)


def upgrade():
    for table in TABLES:
        op.alter_column(table, "organization_id", nullable=True)
    op.drop_constraint(
        "conversation_read_projections_pkey", "conversation_read_projections", type_="primary"
    )
    op.alter_column("conversation_read_projections", "organization_id", nullable=True)
    op.create_primary_key(
        "conversation_read_projections_pkey",
        "conversation_read_projections",
        ["conversation_id", "member_id"],
    )
    if "personal_direct_unique" not in {
        x["name"] for x in sa.inspect(op.get_bind()).get_indexes("conversations")
    }:
        op.create_index(
            "personal_direct_unique",
            "conversations",
            ["direct_key"],
            unique=True,
            postgresql_where=sa.text("organization_id IS NULL"),
        )
    if "personal_direct_only" not in {
        x["name"] for x in sa.inspect(op.get_bind()).get_check_constraints("conversations")
    }:
        op.create_check_constraint(
            "personal_direct_only",
            "conversations",
            "organization_id IS NOT NULL OR (type = 'DIRECT' AND direct_key IS NOT NULL)",
        )


def downgrade():
    # Refuse loss of personal data; callers must deliberately migrate it before downgrade.
    op.alter_column("conversation_read_projections", "organization_id", nullable=False)
    for table in TABLES:
        op.alter_column(table, "organization_id", nullable=False)
    op.drop_constraint(
        "conversation_read_projections_pkey", "conversation_read_projections", type_="primary"
    )
    op.create_primary_key(
        "conversation_read_projections_pkey",
        "conversation_read_projections",
        ["organization_id", "conversation_id", "member_id"],
    )
    op.drop_constraint("personal_direct_only", "conversations", type_="check")
    op.drop_index("personal_direct_unique", table_name="conversations")
