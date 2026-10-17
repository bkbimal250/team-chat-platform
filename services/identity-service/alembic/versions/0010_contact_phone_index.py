"""Private exact phone matching index; populate using contact_phone_backfill."""

import sqlalchemy as sa

from alembic import op

revision = "0010_contact_phone_index"
down_revision = "0009_personal_accounts"
branch_labels = None
depends_on = None


def upgrade():
    # 0001 applies current metadata on a fresh database.
    inspector = sa.inspect(op.get_bind())
    if "contact_phone_digest" not in {
        column["name"] for column in inspector.get_columns("identities")
    }:
        op.add_column("identities", sa.Column("contact_phone_digest", sa.String(64), nullable=True))
    if "ix_identities_contact_phone_digest" not in {
        index["name"] for index in inspector.get_indexes("identities")
    }:
        op.create_index(
            "ix_identities_contact_phone_digest", "identities", ["contact_phone_digest"], unique=True
        )


def downgrade():
    op.drop_index("ix_identities_contact_phone_digest", table_name="identities")
    op.drop_column("identities", "contact_phone_digest")
