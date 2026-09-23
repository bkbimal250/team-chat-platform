import json
import logging
from datetime import UTC, datetime

from app.core.config import Settings


class JsonFormatter(logging.Formatter):
    def __init__(self, settings: Settings):
        super().__init__()
        self.settings = settings

    def format(self, record: logging.LogRecord) -> str:
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": self.settings.service_name,
            "environment": self.settings.app_env,
            "message": record.getMessage(),
        }
        for field in (
            "correlation_id",
            "identity_id",
            "organization_id",
            "member_id",
            "session_id",
            "device_id",
            "path",
            "method",
            "status",
            "duration_ms",
            "event_id",
            "error_type",
        ):
            if hasattr(record, field):
                data[field] = str(getattr(record, field))
        return json.dumps(data)


def configure_logging(settings: Settings) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(settings))
    logging.basicConfig(level="INFO", handlers=[handler], force=True)
