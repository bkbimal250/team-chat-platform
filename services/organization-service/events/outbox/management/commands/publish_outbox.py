import logging
import time

from django.core.management.base import BaseCommand

from events.outbox.worker import publish_one
from events.publishers.rabbitmq import RabbitPublisher


class Command(BaseCommand):
    help = "Publish committed outbox events with bounded exponential retry."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **options):
        while True:
            try:
                with RabbitPublisher() as publisher:
                    while publish_one(publisher):
                        pass
            except Exception as exc:
                logging.getLogger(__name__).warning(
                    "broker_unavailable", extra={"error_type": type(exc).__name__}
                )
                if options["once"]:
                    raise
            if options["once"]:
                return
            time.sleep(2)
