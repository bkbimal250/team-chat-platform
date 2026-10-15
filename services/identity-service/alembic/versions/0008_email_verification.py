"""Add opaque email-verification challenges and an explicit verified timestamp."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0008_email_verification"
down_revision = "0007_password_recovery"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "identities", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.create_table(
        "email_verification_challenges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("token_hash", sa.String(length=256), nullable=False, unique=True),
        sa.Column("requested_ip", sa.String(length=64), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["identity_id"], ["identities.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "email_verification_identity_active",
        "email_verification_challenges",
        ["identity_id", "consumed_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("email_verification_identity_active", table_name="email_verification_challenges")
    op.drop_table("email_verification_challenges")
    op.drop_column("identities", "email_verified_at")
