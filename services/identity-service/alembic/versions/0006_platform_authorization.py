"""Independent persistent platform grants and safe operator audit."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0006_platform_authorization"
down_revision = "0005_email_password"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not inspector.has_table("platform_grants"):
        op.create_table(
            "platform_grants",
            sa.Column(
                "identity_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("identities.id", ondelete="RESTRICT"),
                primary_key=True,
            ),
            sa.Column("role", sa.String(20), nullable=False),
            sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.CheckConstraint("role IN ('SUPER_ADMIN', 'ADMIN')", name="platform_grant_role"),
        )
    if not inspector.has_table("platform_audit"):
        op.create_table(
            "platform_audit",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("actor", sa.String(200), nullable=False),
            sa.Column("action", sa.String(80), nullable=False),
            sa.Column("target", postgresql.UUID(as_uuid=True), nullable=False),
            sa.Column("result", sa.String(20), nullable=False),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )


def downgrade():
    op.drop_table("platform_audit")
    op.drop_table("platform_grants")
