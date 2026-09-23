import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from events.outbox.models import OutboxEvent


def publish_one(publisher) -> bool:
    """Hold a SKIP LOCKED row lock through confirm. Crash rollback makes it retryable.

    A crash after broker confirmation may duplicate delivery, always with the SAME event_id.
    PROCESSING never commits independently, so there are no stranded processing leases.
    """
    with transaction.atomic():
        event = (
            OutboxEvent.objects.select_for_update(skip_locked=True)
            .filter(status="PENDING", available_at__lte=timezone.now())
            .order_by("created_at", "id")
            .first()
        )
        if event is None:
            return False
        event.status = "PROCESSING"
        event.save(update_fields=["status"])
        try:
            publisher.publish(event)
        except Exception as exc:
            event.retry_count += 1
            event.status = (
                "FAILED" if event.retry_count >= settings.OUTBOX_MAX_RETRIES else "PENDING"
            )
            event.available_at = timezone.now() + timedelta(seconds=min(2**event.retry_count, 3600))
            event.last_error = type(
                exc
            ).__name__  # never persist credentials embedded in exception text
            logging.getLogger(__name__).warning(
                "outbox_publish_failed",
                extra={"event_id": event.event_id, "error_type": event.last_error},
            )
        else:
            event.status = "PUBLISHED"
            event.published_at = timezone.now()
            event.last_error = ""
        event.save()
    return True
