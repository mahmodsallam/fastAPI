from typing import Any

from pydantic import BaseModel


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any | None = None


class ErrorResponse(BaseModel):
    """The single error shape returned by every non-2xx response."""

    error: ErrorBody
