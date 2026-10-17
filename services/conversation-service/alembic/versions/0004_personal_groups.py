"""Allow personal GROUP conversations (organization_id null)."""

import sqlalchemy as sa

from alembic import op

revision = "0004_personal_groups"
down_revision = "0003_personal_direct"
branch_labels = depends_on = None


def upgrade():
    # 0001 applies current metadata, which already uses personal_scope.
    checks = {item["name"] for item in sa.inspect(op.get_bind()).get_check_constraints("conversations")}
    if "personal_direct_only" in checks:
        op.drop_constraint("personal_direct_only", "conversations", type_="check")
    if "personal_scope" not in checks:
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
