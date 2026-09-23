from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.invitations.models import Invitation
from apps.organizations.models import Organization
from common.context import TenantContext
from common.services import record


class Command(BaseCommand):
    help = "Materialize expired invitations in bounded batches (acceptance always checks time)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=500)

    def handle(self, *args, **options):
        candidates = list(
            Invitation.objects.filter(status="PENDING", expires_at__lte=timezone.now())
            .order_by("expires_at")
            .values_list("id", "organization_id")[: max(0, min(options["limit"], 5000))]
        )
        count = 0
        for invitation_id, organization_id in candidates:
            with transaction.atomic():
                Organization.objects.select_for_update().get(id=organization_id)
                invitation = Invitation.objects.select_for_update().get(id=invitation_id)
                if invitation.status != "PENDING" or invitation.expires_at > timezone.now():
                    continue
                invitation.status = "EXPIRED"
                invitation.save()
                record(
                    TenantContext(organization_id, None),
                    invitation,
                    "invitation",
                    "expired",
                    ["status"],
                )
                count += 1
        self.stdout.write(f"Expired {count} invitations.")
