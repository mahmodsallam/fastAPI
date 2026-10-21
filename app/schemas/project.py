from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import StrictInput


class ProjectCreate(StrictInput):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)


class ProjectUpdate(ProjectCreate):
    """PUT is a full replacement, so it takes the same fields as create."""


class ProjectRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime
