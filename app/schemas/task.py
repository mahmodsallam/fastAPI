from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.base import StrictInput


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(StrictInput):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    status: TaskStatus = TaskStatus.TODO


class TaskUpdate(TaskCreate):
    """PUT is a full replacement, so it takes the same fields as create."""


class TaskRead(BaseModel):
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime
