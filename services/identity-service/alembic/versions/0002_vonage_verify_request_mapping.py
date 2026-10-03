"""Persist external Verify request identifiers for OTP challenges."""

import sqlalchemy as sa

from alembic import op

revision = "0002_vonage_verify_request_mapping"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Alembic creates version_num as VARCHAR(32) by default, while this
    # descriptive revision identifier is 36 characters long. Widen it before
    # Alembic records the new revision at the end of this transaction.
    op.alter_column(
        "alembic_version",
        "version_num",
        existing_type=sa.String(length=32),
        type_=sa.String(length=64),
        existing_nullable=False,
    )
    op.add_column(
        "otp_challenges", sa.Column("provider_request_id", sa.String(length=128), nullable=True)
    )
    op.create_index("otp_provider_request", "otp_challenges", ["provider_request_id"], unique=True)


def downgrade() -> None:
    op.drop_index("otp_provider_request", table_name="otp_challenges")
    op.drop_column("otp_challenges", "provider_request_id")
