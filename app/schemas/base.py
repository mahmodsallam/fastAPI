from pydantic import BaseModel, ConfigDict


class StrictInput(BaseModel):
    """Base for request bodies: trim strings and reject unknown fields."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
