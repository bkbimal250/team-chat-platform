"""message e2ee envelope column"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "0005_message_e2ee_envelope"
down_revision = "0004_fwd_broadcast_org"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("messages", sa.Column("e2ee_envelope", JSONB, nullable=True))


def downgrade():
    op.drop_column("messages", "e2ee_envelope")
