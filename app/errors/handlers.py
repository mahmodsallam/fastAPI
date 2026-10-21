import logging
from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors.exceptions import AppError
from app.errors.models import ErrorBody, ErrorResponse

logger = logging.getLogger(__name__)


def _envelope(
    status_code: int, code: str, message: str, details: Any | None = None
) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump())


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return _envelope(exc.status_code, exc.code, exc.message, exc.details)


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    # Covers framework-raised errors too, e.g. unknown route (404), wrong verb (405).
    try:
        code = HTTPStatus(exc.status_code).phrase.lower().replace(" ", "_")
    except ValueError:
        code = "http_error"
    message = exc.detail if isinstance(exc.detail, str) else code.replace("_", " ")
    return _envelope(exc.status_code, code, message)


async def validation_error_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # exc.errors() can carry raw input and exception objects; expose only safe fields.
    details = [
        {
            "field": ".".join(str(part) for part in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]
    return _envelope(422, "validation_error", "Request validation failed", details)


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return _envelope(500, "internal_error", "Internal server error")


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
