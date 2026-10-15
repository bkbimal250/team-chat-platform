"""Private exact phone matching index; populate using contact_phone_backfill."""

import sqlalchemy as sa

from alembic import op

revision = "0010_contact_phone_index"
down_revision = "0009_personal_accounts"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("identities", sa.Column("contact_phone_digest", sa.String(64), nullable=True))
    op.create_index(
        "ix_identities_contact_phone_digest", "identities", ["contact_phone_digest"], unique=True
    )


def downgrade():
    op.drop_index("ix_identities_contact_phone_digest", table_name="identities")
    op.drop_column("identities", "contact_phone_digest")
