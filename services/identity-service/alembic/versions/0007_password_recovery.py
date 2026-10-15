"""Add one-time, hashed password recovery challenges."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "0007_password_recovery"
down_revision = "0006_platform_authorization"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "password_reset_challenges",
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
        "password_reset_identity_active",
        "password_reset_challenges",
        ["identity_id", "consumed_at", "expires_at"],
    )


def downgrade() -> None:
    op.drop_index("password_reset_identity_active", table_name="password_reset_challenges")
    op.drop_table("password_reset_challenges")
