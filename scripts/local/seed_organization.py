"""Operator setup of an explicit local workspace, retaining invite-only policy."""

import os
from uuid import NAMESPACE_URL, uuid5

import django

if "127.0.0.1:5434/teamchat_organization_db" not in os.environ.get("DATABASE_URL", ""):
    raise RuntimeError("Seed is restricted to isolated local development")
django.setup()
from apps.members.models import Member
from apps.organizations.models import Organization
from apps.organizations.services import provision_organization
from apps.roles.models import Role, RoleAssignment
from common.authorization import PERMISSIONS
from common.context import TenantContext
from common.services import record
from django.db import transaction
from django.utils import timezone

with transaction.atomic():
    organization = Organization.objects.filter(slug="globalchat-local").first()
    alice = uuid5(NAMESPACE_URL, "globalchat-local:+919000000001")
    if organization is None:
        organization, owner = provision_organization(
            name="GlobalChat Local",
            slug="globalchat-local",
            owner_name="Local Alice",
            owner_user_id=alice,
        )
    else:
        owner = Member.objects.get(organization=organization, user_id=alice)
    bob_id = uuid5(NAMESPACE_URL, "globalchat-local:+919000000002")
    bob = Member.objects.filter(organization=organization, user_id=bob_id).first()
    if bob is None:
        bob = Member.objects.create(
            organization=organization,
            user_id=bob_id,
            display_name="Local Bob",
            status="ACTIVE",
            joined_at=timezone.now(),
        )
        RoleAssignment.objects.create(
            organization=organization,
            member=bob,
            role=Role.objects.get(organization=organization, kind="MEMBER"),
        )
        context = TenantContext(organization.id, owner.id, owner.user_id, PERMISSIONS)
        record(context, bob, "member", "created")
        record(context, bob, "member", "activated", ["status"])
print("Explicit local workspace and two active members ready")
