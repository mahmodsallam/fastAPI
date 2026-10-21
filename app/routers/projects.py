from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_store
from app.errors import AppError, error_responses
from app.repository import InMemoryStore, ProjectRecord
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

Store = Annotated[InMemoryStore, Depends(get_store)]

NOT_FOUND = {404: "Project not found"}
INVALID = {422: "Validation error: malformed id or invalid request body"}


def project_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "project_not_found", "Project not found")


def get_project_or_404(store: InMemoryStore, project_id: UUID) -> ProjectRecord:
    record = store.get_project(project_id)
    if record is None:
        raise project_not_found()
    return record


@router.post(
    "",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a project",
    responses=error_responses(INVALID),
)
def create_project(data: ProjectCreate, store: Store) -> ProjectRecord:
    """Create a project from a name (1-120 chars) and an optional description
    (max 2000 chars). Surrounding whitespace is trimmed and unknown fields are
    rejected. The server assigns the `id` and both timestamps."""
    return store.create_project(data)


@router.get(
    "",
    response_model=list[ProjectRead],
    summary="List projects",
)
def list_projects(store: Store) -> list[ProjectRecord]:
    """Return all projects, oldest first. Pagination arrives in a later milestone."""
    return store.list_projects()


@router.get(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Get a project",
    responses=error_responses(NOT_FOUND | INVALID),
)
def get_project(project_id: UUID, store: Store) -> ProjectRecord:
    """Return one project by its UUID."""
    return get_project_or_404(store, project_id)


@router.put(
    "/{project_id}",
    response_model=ProjectRead,
    summary="Replace a project's editable fields",
    responses=error_responses(NOT_FOUND | INVALID),
)
def update_project(
    project_id: UUID, data: ProjectUpdate, store: Store
) -> ProjectRecord:
    """Fully replace the project's editable fields (`name`, `description`).

    This is a full replacement, not a partial update: an omitted `description`
    is reset to `null`. `id` and `created_at` never change; `updated_at` is
    refreshed."""
    record = store.update_project(project_id, data)
    if record is None:
        raise project_not_found()
    return record


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a project",
    responses=error_responses(NOT_FOUND | INVALID),
)
def delete_project(project_id: UUID, store: Store) -> None:
    """Delete the project and, by cascade, every task that belongs to it.
    Returns 204 with no body; deleting an already-deleted project is a 404."""
    if not store.delete_project(project_id):
        raise project_not_found()
