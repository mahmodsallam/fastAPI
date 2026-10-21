from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_store
from app.errors import AppError, error_responses
from app.repository import InMemoryStore, TaskRecord
from app.routers.projects import get_project_or_404
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

Store = Annotated[InMemoryStore, Depends(get_store)]

PROJECT_NOT_FOUND = {404: "Project not found"}
TASK_NOT_FOUND = {404: "Project not found, or task not found in that project"}
INVALID = {422: "Validation error: malformed id or invalid request body"}


def task_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "task_not_found", "Task not found")


@router.post(
    "",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a task in a project",
    responses=error_responses(PROJECT_NOT_FOUND | INVALID),
)
def create_task(project_id: UUID, data: TaskCreate, store: Store) -> TaskRecord:
    """Create a task with a title (1-200 chars), an optional description
    (max 2000 chars) and a status (`todo`, `in_progress` or `done`; default
    `todo`). The task's `project_id` comes from the URL and cannot be sent in
    the body."""
    get_project_or_404(store, project_id)
    return store.create_task(project_id, data)


@router.get(
    "",
    response_model=list[TaskRead],
    summary="List a project's tasks",
    responses=error_responses(PROJECT_NOT_FOUND | INVALID),
)
def list_tasks(project_id: UUID, store: Store) -> list[TaskRecord]:
    """Return the project's tasks, oldest first. Filtering, sorting and
    pagination arrive in a later milestone."""
    get_project_or_404(store, project_id)
    return store.list_tasks(project_id)


@router.get(
    "/{task_id}",
    response_model=TaskRead,
    summary="Get a task",
    responses=error_responses(TASK_NOT_FOUND | INVALID),
)
def get_task(project_id: UUID, task_id: UUID, store: Store) -> TaskRecord:
    """Return one task. A task that belongs to a different project is reported
    as not found."""
    get_project_or_404(store, project_id)
    record = store.get_task(project_id, task_id)
    if record is None:
        raise task_not_found()
    return record


@router.put(
    "/{task_id}",
    response_model=TaskRead,
    summary="Replace a task's editable fields",
    responses=error_responses(TASK_NOT_FOUND | INVALID),
)
def update_task(
    project_id: UUID, task_id: UUID, data: TaskUpdate, store: Store
) -> TaskRecord:
    """Fully replace the task's editable fields (`title`, `description`,
    `status`).

    This is a full replacement, not a partial update: an omitted `description`
    is reset to `null` and an omitted `status` to `todo`. A task cannot be
    moved to another project. `updated_at` is refreshed."""
    get_project_or_404(store, project_id)
    record = store.update_task(project_id, task_id, data)
    if record is None:
        raise task_not_found()
    return record


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    responses=error_responses(TASK_NOT_FOUND | INVALID),
)
def delete_task(project_id: UUID, task_id: UUID, store: Store) -> None:
    """Delete one task. Returns 204 with no body; deleting an already-deleted
    task is a 404."""
    get_project_or_404(store, project_id)
    if not store.delete_task(project_id, task_id):
        raise task_not_found()
