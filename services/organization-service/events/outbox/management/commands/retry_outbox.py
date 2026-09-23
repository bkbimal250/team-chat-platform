from uuid import UUID

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from events.outbox.models import OutboxEvent


class Command(BaseCommand):
    help = "Requeue one failed event; preserve its event_id for consumer deduplication."

    def add_arguments(self, parser):
        parser.add_argument("event_id", type=UUID)

    @transaction.atomic
    def handle(self, *args, **options):
        event = OutboxEvent.objects.select_for_update().get(
            event_id=options["event_id"], status="FAILED"
        )
        event.status = "PENDING"
        event.retry_count = 0
        event.available_at = timezone.now()
        event.save()
        self.stdout.write("Event requeued.")
