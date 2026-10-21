from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """The single error shape returned by every non-2xx response."""

    error: ErrorBody


def error_responses(descriptions: dict[int, str]) -> dict[int | str, dict[str, Any]]:
    """Build the `responses=` argument for a route so OpenAPI shows ErrorResponse."""
    return {
        status: {"model": ErrorResponse, "description": description}
        for status, description in descriptions.items()
    }
