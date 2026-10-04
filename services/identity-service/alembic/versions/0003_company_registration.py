"""Durable company registration orchestration."""

from alembic import op
from app.models.models import CompanyRegistration

revision = "0003_company_registration"
down_revision = "0002_vonage_verify_request_mapping"
branch_labels = None
depends_on = None


def upgrade():
    CompanyRegistration.__table__.create(op.get_bind(), checkfirst=True)


def downgrade():
    CompanyRegistration.__table__.drop(op.get_bind())
