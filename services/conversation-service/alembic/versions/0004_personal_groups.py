"""Allow personal GROUP conversations (organization_id null)."""

import sqlalchemy as sa

from alembic import op

revision = "0004_personal_groups"
down_revision = "0003_personal_direct"
branch_labels = depends_on = None


def upgrade():
    op.drop_constraint("personal_direct_only", "conversations", type_="check")
    op.create_check_constraint(
        "personal_scope",
        "conversations",
        "organization_id IS NOT NULL OR (type = 'GROUP') OR (type = 'DIRECT' AND direct_key IS NOT NULL)",
    )


def downgrade():
    op.drop_constraint("personal_scope", "conversations", type_="check")
    op.create_check_constraint(
        "personal_direct_only",
        "conversations",
        "organization_id IS NOT NULL OR (type = 'DIRECT' AND direct_key IS NOT NULL)",
    )
