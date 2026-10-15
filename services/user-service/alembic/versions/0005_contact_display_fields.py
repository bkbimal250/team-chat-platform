"""Owner-visible contact names and formatted phone display."""

import sqlalchemy as sa

from alembic import op

revision = "0005_contact_display_fields"
down_revision = "0004_profile_photo_expiry"
branch_labels = depends_on = None


def upgrade():
    op.add_column("contacts", sa.Column("given_name", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("family_name", sa.String(100), nullable=True))
    op.add_column("contacts", sa.Column("phone_display", sa.String(40), nullable=True))


def downgrade():
    op.drop_column("contacts", "phone_display")
    op.drop_column("contacts", "family_name")
    op.drop_column("contacts", "given_name")
