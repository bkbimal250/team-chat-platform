"""Device E2EE public key material (Signal Protocol)."""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0011_device_e2ee_keys"
down_revision = "0010_contact_phone_index"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "device_e2ee_bundles",
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("identity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("registration_id", sa.Integer(), nullable=False),
        sa.Column("identity_key_public", sa.LargeBinary(), nullable=False),
        sa.Column("key_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("signed_prekey_id", sa.Integer(), nullable=False),
        sa.Column("signed_prekey_public", sa.LargeBinary(), nullable=False),
        sa.Column("signed_prekey_signature", sa.LargeBinary(), nullable=False),
        sa.Column("kyber_prekey_id", sa.Integer(), nullable=False),
        sa.Column("kyber_prekey_public", sa.LargeBinary(), nullable=False),
        sa.Column("kyber_prekey_signature", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "rotated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["identity_id"], ["identities.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("device_id"),
        sa.CheckConstraint(
            "registration_id BETWEEN 1 AND 16383", name="e2ee_registration_id_range"
        ),
    )
    op.create_index("ix_device_e2ee_identity", "device_e2ee_bundles", ["identity_id"])

    op.create_table(
        "device_one_time_prekeys",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("prekey_id", sa.Integer(), nullable=False),
        sa.Column("public_key", sa.LargeBinary(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "prekey_id", name="device_prekey_id_unique"),
    )
    op.create_index(
        "ix_device_prekeys_available",
        "device_one_time_prekeys",
        ["device_id"],
        postgresql_where=sa.text("consumed_at IS NULL"),
    )


def downgrade():
    op.drop_index("ix_device_prekeys_available", table_name="device_one_time_prekeys")
    op.drop_table("device_one_time_prekeys")
    op.drop_index("ix_device_e2ee_identity", table_name="device_e2ee_bundles")
    op.drop_table("device_e2ee_bundles")
