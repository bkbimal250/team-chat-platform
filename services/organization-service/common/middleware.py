import json
import logging
import re
import time
from datetime import UTC, datetime

from django.conf import settings

from common.ids import new_id


class JsonFormatter(logging.Formatter):
    def format(self, record):
        data = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "service": settings.SERVICE_NAME,
            "environment": settings.ENVIRONMENT,
            "message": record.getMessage(),
        }
        for key in (
            "correlation_id",
            "organization_id",
            "user_id",
            "member_id",
            "path",
            "method",
            "status",
            "duration_ms",
            "error_type",
            "event_id",
        ):
            if hasattr(record, key):
                data[key] = getattr(record, key)
        return json.dumps(data, default=str)


class RequestLoggingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        supplied = request.headers.get("X-Correlation-ID", "")
        request.correlation_id = (
            supplied if re.fullmatch(r"[A-Za-z0-9._:-]{1,128}", supplied) else str(new_id())
        )
        start = time.monotonic()
        response = self.get_response(request)
        response["X-Correlation-ID"] = request.correlation_id
        ctx = getattr(request, "tenant_context", None)
        logging.getLogger("requests").info(
            "http_request",
            extra={
                "correlation_id": request.correlation_id,
                "path": request.path,
                "method": request.method,
                "status": response.status_code,
                "duration_ms": round((time.monotonic() - start) * 1000, 2),
                **{
                    key: getattr(ctx, key, None)
                    for key in ("organization_id", "user_id", "member_id")
                },
            },
        )
        return response
