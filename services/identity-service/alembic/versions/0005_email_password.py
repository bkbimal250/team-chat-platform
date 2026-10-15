"""Add password credentials without changing existing OTP data."""

import sqlalchemy as sa

from alembic import op

revision = "0005_email_password"
down_revision = "0004_invitation_onboarding"
branch_labels = None
depends_on = None


def upgrade():
    inspector = sa.inspect(op.get_bind())
    identity_columns = {column["name"] for column in inspector.get_columns("identities")}
    identity_indexes = {index["name"] for index in inspector.get_indexes("identities")}
    if "password_hash" not in identity_columns:
        op.add_column("identities", sa.Column("password_hash", sa.String(256), nullable=True))
    # Abort on conflicting historical addresses; never merge identities silently.
    if "identity_canonical_email" not in identity_indexes:
        op.create_index(
            "identity_canonical_email", "identities", [sa.text("lower(trim(email))")], unique=True
        )
    op.alter_column("company_registrations", "challenge_id", nullable=True)
    op.alter_column("invitation_onboardings", "challenge_id", nullable=True)


def downgrade():
    # OTP-less registration intents cannot safely regain a NOT NULL constraint.
    bind = op.get_bind()
    if bind.execute(
        sa.text(
            "SELECT 1 FROM company_registrations WHERE challenge_id IS NULL UNION ALL SELECT 1 FROM invitation_onboardings WHERE challenge_id IS NULL LIMIT 1"
        )
    ).first():
        raise RuntimeError("Cannot downgrade while email registration intents exist")
    op.alter_column("company_registrations", "challenge_id", nullable=False)
    op.alter_column("invitation_onboardings", "challenge_id", nullable=False)
    op.drop_index("identity_canonical_email", table_name="identities")
    op.drop_column("identities", "password_hash")
