"""Private account profile photos independent of conversations."""
import sqlalchemy as sa

from alembic import op

revision = "0005_profile_photos"
down_revision = "0004_references_revocation"
branch_labels = depends_on = None

def upgrade():
    op.create_table("profile_photos",
        sa.Column("id", sa.UUID(), primary_key=True),
        sa.Column("owner_identity_id", sa.UUID(), nullable=False),
        sa.Column("object_key", sa.String(512), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(32), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_profile_photos_owner_identity_id", "profile_photos", ["owner_identity_id"])

def downgrade():
    op.drop_table("profile_photos")
