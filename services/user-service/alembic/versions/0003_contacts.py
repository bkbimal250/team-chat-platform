"""Private user-owned contacts and discoverability."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0003_contacts"
down_revision = "0002_outbox_delivery_state"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_privacy_settings",
        sa.Column("discoverable", sa.Boolean(), nullable=False, server_default=sa.true()),
    )
    op.create_table(
        "contacts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("phone_digest", sa.String(64), nullable=False),
        sa.Column("local_label", sa.String(200)),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("owner_user_id", "phone_digest", name="contact_owner_phone_unique"),
    )

    op.create_index("contact_owner_listing", "contacts", ["owner_user_id", "id"])


def downgrade():
    op.drop_index("contact_owner_listing", table_name="contacts", if_exists=True)
    op.drop_table("contacts")
    op.drop_column("user_privacy_settings", "discoverable")
