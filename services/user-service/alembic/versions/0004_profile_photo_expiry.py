"""Server-authoritative temporary profile picture expiry."""
import sqlalchemy as sa

from alembic import op

revision = "0004_profile_photo_expiry"
down_revision = "0003_contacts"
branch_labels = depends_on = None

def upgrade():
    # 0001 applies current metadata on a fresh database.
    columns = {column["name"] for column in sa.inspect(op.get_bind()).get_columns("users")}
    if "avatar_expires_at" not in columns:
        op.add_column("users", sa.Column("avatar_expires_at", sa.DateTime(timezone=True), nullable=True))

def downgrade():
    op.drop_column("users", "avatar_expires_at")
