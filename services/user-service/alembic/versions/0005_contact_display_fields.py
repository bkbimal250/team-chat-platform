"""Owner-visible contact names and formatted phone display."""

import sqlalchemy as sa

from alembic import op

revision = "0005_contact_display_fields"
down_revision = "0004_profile_photo_expiry"
branch_labels = depends_on = None


def upgrade():
    # 0001 applies current metadata on a fresh database.
    existing = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("contacts")}
    for name, length in (("given_name", 100), ("family_name", 100), ("phone_display", 40)):
        if name not in existing:
            op.add_column("contacts", sa.Column(name, sa.String(length), nullable=True))


def downgrade():
    op.drop_column("contacts", "phone_display")
    op.drop_column("contacts", "family_name")
    op.drop_column("contacts", "given_name")
