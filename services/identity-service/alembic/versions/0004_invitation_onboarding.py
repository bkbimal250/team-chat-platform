"""Durable invitation acceptance intent."""

from alembic import op
from app.models.models import InvitationOnboarding

revision = "0004_invitation_onboarding"
down_revision = "0003_company_registration"
branch_labels = None
depends_on = None


def upgrade():
    InvitationOnboarding.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    InvitationOnboarding.__table__.drop(op.get_bind())
