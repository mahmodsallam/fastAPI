from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_store
from app.errors import AppError
from app.repository import InMemoryStore, ProjectRecord
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])

Store = Annotated[InMemoryStore, Depends(get_store)]


def project_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "project_not_found", "Project not found")


def get_project_or_404(store: InMemoryStore, project_id: UUID) -> ProjectRecord:
    record = store.get_project(project_id)
    if record is None:
        raise project_not_found()
    return record


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, store: Store) -> ProjectRecord:
    return store.create_project(data)


@router.get("", response_model=list[ProjectRead])
def list_projects(store: Store) -> list[ProjectRecord]:
    return store.list_projects()


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: UUID, store: Store) -> ProjectRecord:
    return get_project_or_404(store, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: UUID, data: ProjectUpdate, store: Store
) -> ProjectRecord:
    record = store.update_project(project_id, data)
    if record is None:
        raise project_not_found()
    return record


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: UUID, store: Store) -> None:
    if not store.delete_project(project_id):
        raise project_not_found()
