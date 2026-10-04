import json
import logging

from app.core.config import get_settings
from app.core.logging import JsonFormatter


def test_identity_request_formatter_uses_configured_service_without_exception():
    record = logging.LogRecord("requests", logging.INFO, "", 1, "http_request", (), None)
    record.path = "/api/v1/auth/registration/company/start"
    record.status = 202
    formatted = json.loads(JsonFormatter(get_settings()).format(record))
    assert formatted["service"] == get_settings().SERVICE_NAME
    assert formatted["path"] == record.path
    assert formatted["message"] == "http_request"
