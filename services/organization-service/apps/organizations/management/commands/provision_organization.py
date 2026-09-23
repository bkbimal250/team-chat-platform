from uuid import UUID

from django.core.management.base import BaseCommand

from apps.organizations.services import provision_organization


class Command(BaseCommand):
    help = "Provision a tenant and its owner (operator-only bootstrap command)."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--slug", required=True)
        parser.add_argument("--owner-name", required=True)
        parser.add_argument("--owner-user-id", required=True, type=UUID)

    def handle(self, *args, **options):
        organization, owner = provision_organization(
            name=options["name"],
            slug=options["slug"],
            owner_name=options["owner_name"],
            owner_user_id=options["owner_user_id"],
        )
        self.stdout.write(f"organization_id={organization.id}\nowner_member_id={owner.id}")
