from uuid import UUID

from django.core.management.base import BaseCommand

from apps.organizations.services import set_organization_status
from common.context import TenantContext


class Command(BaseCommand):
    help = "Operator lifecycle transition, including recovery of suspended/disabled tenants."

    def add_arguments(self, parser):
        parser.add_argument("organization_id", type=UUID)
        parser.add_argument("status", choices=["ACTIVE", "SUSPENDED", "DISABLED", "DELETED"])

    def handle(self, *args, **options):
        context = TenantContext(options["organization_id"], None)
        result = set_organization_status(context, options["status"], operator=True)
        self.stdout.write(f"{result.id}: {result.status}")
