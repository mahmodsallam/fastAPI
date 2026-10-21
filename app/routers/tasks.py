from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.dependencies import get_store
from app.errors import AppError
from app.repository import InMemoryStore, TaskRecord
from app.routers.projects import get_project_or_404
from app.schemas import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

Store = Annotated[InMemoryStore, Depends(get_store)]


def task_not_found() -> AppError:
    return AppError(status.HTTP_404_NOT_FOUND, "task_not_found", "Task not found")


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(project_id: UUID, data: TaskCreate, store: Store) -> TaskRecord:
    get_project_or_404(store, project_id)
    return store.create_task(project_id, data)


@router.get("", response_model=list[TaskRead])
def list_tasks(project_id: UUID, store: Store) -> list[TaskRecord]:
    get_project_or_404(store, project_id)
    return store.list_tasks(project_id)


@router.get("/{task_id}", response_model=TaskRead)
def get_task(project_id: UUID, task_id: UUID, store: Store) -> TaskRecord:
    get_project_or_404(store, project_id)
    record = store.get_task(project_id, task_id)
    if record is None:
        raise task_not_found()
    return record


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    project_id: UUID, task_id: UUID, data: TaskUpdate, store: Store
) -> TaskRecord:
    get_project_or_404(store, project_id)
    record = store.update_task(project_id, task_id, data)
    if record is None:
        raise task_not_found()
    return record


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(project_id: UUID, task_id: UUID, store: Store) -> None:
    get_project_or_404(store, project_id)
    if not store.delete_task(project_id, task_id):
        raise task_not_found()
