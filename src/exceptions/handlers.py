from __future__ import annotations

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from src.exceptions.domain import ClinicBookingException


async def clinic_booking_exception_handler(request: Request, exc: ClinicBookingException) -> JSONResponse:
    """Handle domain business exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.message},
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Format Pydantic request validation errors into a single readable error string."""
    errors = exc.errors()
    if errors:
        first_err = errors[0]
        # Build field path omitting the internal 'body' token
        loc_parts = [str(part) for part in first_err.get("loc", []) if part != "body"]
        field_name = " -> ".join(loc_parts)
        raw_msg = first_err.get("msg", "Invalid value")
        # Strip ValueError prefix if added by Pydantic
        if raw_msg.startswith("Value error, "):
            raw_msg = raw_msg[len("Value error, "):]
        error_message = f"{field_name}: {raw_msg}" if field_name else raw_msg
    else:
        error_message = "Invalid request payload"

    return JSONResponse(
        status_code=400,
        content={"error": error_message},
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle standard HTTP exceptions with uniform error responses."""
    detail = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": detail},
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom exception handlers on the FastAPI application instance."""
    app.add_exception_handler(ClinicBookingException, clinic_booking_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
