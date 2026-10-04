"""Isolated local cross-tenant fixture; never grants frontend authorization."""
import json
import os
from pathlib import Path
from uuid import uuid4

import django

if os.environ.get("APP_ENV") != "development" or "127.0.0.1:5434/teamchat_organization_db" not in os.environ.get("DATABASE_URL", ""):
    raise RuntimeError("Isolated local database required")
django.setup()
from apps.organizations.models import Organization
from apps.organizations.services import provision_organization
from apps.branches.models import Branch
from django.db import transaction

root = Path(__file__).resolve().parents[4]
with transaction.atomic():
    foreign = Organization.objects.filter(slug="admin-security-fixture").first()
    if foreign is None:
        foreign, _ = provision_organization(name="Local admin security fixture",slug="admin-security-fixture",owner_name="Local fixture owner",owner_user_id=uuid4())
    branch, _ = Branch.objects.get_or_create(organization=foreign,code="SECURITY",defaults={"name":"Foreign tenant fixture","country":"IN"})
(root / ".local/admin-fixtures.json").write_text(json.dumps({"foreign_organization_id":str(foreign.id),"foreign_branch_id":str(branch.id)}),encoding="utf-8")
print("Local cross-tenant fixture ready; no frontend permissions granted")
