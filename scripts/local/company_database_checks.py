"""Read-only physical local onboarding verification; each service owns its database."""
import asyncio
import json
import os
import sys
from pathlib import Path
from uuid import UUID
from urllib.parse import urlparse

root = Path(__file__).resolve().parents[2]
data = json.loads((root / ".local/company-registration-check.json").read_text())
url = urlparse(os.environ["DATABASE_URL"])
assert url.hostname in {"localhost", "127.0.0.1"} and url.port == 5434
service = sys.argv[1]
if service == "organization":
    import django
    django.setup()
    from apps.organizations.models import Organization
    from apps.members.models import Member
    from common.authorization import effective_permissions
    assert Organization.objects.filter(id=data["organization_id"]).count() == 1
    assert Member.objects.filter(organization_id=data["organization_id"]).count() == 1
    owner = Member.objects.get(id=data["member_id"])
    assert "member.create" in effective_permissions(owner)
    print("Physical organization/membership uniqueness and owner authorization PASS")
else:
    from sqlalchemy import select, func
    async def verify():
        if service == "identity":
            from app.db.session import SessionLocal
            from app.models.models import CompanyRegistration, Identity
            async with SessionLocal() as db:
                row = await db.get(CompanyRegistration, UUID(data["registration_id"]))
                assert row.state == "COMPLETED" and str(row.member_id) == data["member_id"]
                identity = await db.get(Identity, row.identity_id)
                assert identity.status == "ACTIVE" and identity.phone_verified
                assert await db.scalar(select(func.count()).select_from(Identity).where(Identity.phone_number == identity.phone_number)) == 1
                data["identity_id"] = str(identity.id)
                (root / ".local/company-registration-check.json").write_text(json.dumps(data))
                print("Physical Identity/registration uniqueness PASS")
        else:
            from app.main import sessions, User
            async with sessions() as db:
                assert await db.scalar(select(func.count()).select_from(User).where(User.identity_id == UUID(data["identity_id"]))) == 1
                print("Physical profile uniqueness PASS")
    asyncio.run(verify())
