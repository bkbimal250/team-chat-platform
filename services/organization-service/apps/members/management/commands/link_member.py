from uuid import UUID

from django.core.management.base import BaseCommand

from apps.members.models import Member
from common.context import TenantContext
from common.selectors import tenant_get
from common.services import command, record


@command
def link(context, member_id, user_id):
    from apps.organizations.models import Organization
    from common.exceptions import DomainError

    Organization.objects.select_for_update().get(id=context.organization_id)
    member = tenant_get(Member, context, member_id, lock=True)
    if member.status != "INVITED" or member.user_id:
        raise DomainError(
            "IDENTITY_ALREADY_LINKED", "Only an unlinked invited member may be linked."
        )
    member.user_id = user_id
    member.save()
    record(context, member, "member", "updated", ["user_id"])


class Command(BaseCommand):
    help = "Operator-only Phase 1 identity reference linking. Does not authenticate the referenced user."

    def add_arguments(self, parser):
        parser.add_argument("organization_id", type=UUID)
        parser.add_argument("member_id", type=UUID)
        parser.add_argument("user_id", type=UUID)

    def handle(self, *args, **options):
        link(
            TenantContext(options["organization_id"], None),
            options["member_id"],
            options["user_id"],
        )
        self.stdout.write("Identity reference linked.")
