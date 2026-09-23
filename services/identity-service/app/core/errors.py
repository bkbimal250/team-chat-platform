from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass
class DomainError(Exception):
    code: str
    message: str
    status_code: int = 409
    details: dict | None = None


async def domain_error_handler(request: Request, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details or {},
                "correlation_id": request.state.correlation_id,
            }
        },
    )
