import logging

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response


class DomainError(APIException):
    status_code = 409
    default_code = "DOMAIN_CONFLICT"

    def __init__(self, code: str, message: str, status: int = 409):
        self.status_code = status
        self.machine_code = code
        super().__init__(message, code=code)


def exception_handler(exc, context):
    from rest_framework.views import exception_handler as drf_exception_handler

    if isinstance(exc, DjangoValidationError):
        exc = ValidationError(getattr(exc, "message_dict", exc.messages))
    if isinstance(exc, IntegrityError):
        exc = DomainError(
            "CONSTRAINT_CONFLICT",
            "The operation conflicts with an existing resource or relationship.",
        )
    response = drf_exception_handler(exc, context)
    if response is None:
        logging.getLogger(__name__).error(
            "unhandled_request_error", extra={"error_type": type(exc).__name__}
        )
        response = Response({"detail": "An internal error occurred."}, status=500)
    code = getattr(exc, "machine_code", getattr(exc, "default_code", "INTERNAL_ERROR")).upper()
    details = response.data
    message = (
        str(details.get("detail", "Request validation failed."))
        if isinstance(details, dict)
        else "Request validation failed."
    )
    response.data = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "correlation_id": getattr(context["request"], "correlation_id", ""),
        }
    }
    return response
