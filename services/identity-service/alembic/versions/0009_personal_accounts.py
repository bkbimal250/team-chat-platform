"""Allow personal sessions and durable profile provisioning without a tenant."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0009_personal_accounts"
down_revision = "0008_email_verification"
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("sessions", "organization_id", nullable=True)
    op.alter_column("sessions", "member_id", nullable=True)
    op.create_check_constraint(
        "session_context_pair", "sessions", "(organization_id IS NULL) = (member_id IS NULL)"
    )
    op.create_table(
        "personal_registrations",
        sa.Column(
            "identity_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("identities.id"),
            primary_key=True,
        ),
        sa.Column("display_name", sa.String(200), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )


def downgrade():
    # Never delete sessions or invent tenant IDs to satisfy the previous schema.
    if (
        op.get_bind()
        .execute(
            sa.text(
                "SELECT EXISTS (SELECT 1 FROM sessions WHERE organization_id IS NULL) OR EXISTS (SELECT 1 FROM personal_registrations)"
            )
        )
        .scalar()
    ):
        raise RuntimeError(
            "Cannot downgrade while personal accounts or sessions exist; preserve data and use a forward migration."
        )
    op.drop_table("personal_registrations")
    op.drop_constraint("session_context_pair", "sessions", type_="check")
    op.alter_column("sessions", "member_id", nullable=False)
    op.alter_column("sessions", "organization_id", nullable=False)
