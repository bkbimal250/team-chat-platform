"""Server-authoritative temporary profile picture expiry."""
import sqlalchemy as sa

from alembic import op

revision = "0004_profile_photo_expiry"
down_revision = "0003_contacts"
branch_labels = depends_on = None

def upgrade():
    op.add_column("users", sa.Column("avatar_expires_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("users", "avatar_expires_at")
