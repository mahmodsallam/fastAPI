from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)


@dataclass
class ProjectRecord:
    id: UUID
    name: str
    description: str | None
    created_at: datetime
    updated_at: datetime


@dataclass
class TaskRecord:
    id: UUID
    project_id: UUID
    title: str
    description: str | None
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class InMemoryStore:
    """Temporary Milestone 1 storage; replaced by PostgreSQL in Milestone 2.

    Methods return None / False for missing rows; the routers decide that
    this means a 404.
    """

    def __init__(self) -> None:
        # dicts keep insertion order, so listing is ordered by creation time.
        self._projects: dict[UUID, ProjectRecord] = {}
        self._tasks: dict[UUID, TaskRecord] = {}

    def create_project(self, data: ProjectCreate) -> ProjectRecord:
        now = datetime.now(UTC)
        record = ProjectRecord(
            id=uuid4(),
            name=data.name,
            description=data.description,
            created_at=now,
            updated_at=now,
        )
        self._projects[record.id] = record
        return record

    def list_projects(self) -> list[ProjectRecord]:
        return list(self._projects.values())

    def get_project(self, project_id: UUID) -> ProjectRecord | None:
        return self._projects.get(project_id)

    def update_project(
        self, project_id: UUID, data: ProjectUpdate
    ) -> ProjectRecord | None:
        record = self._projects.get(project_id)
        if record is None:
            return None
        record.name = data.name
        record.description = data.description
        record.updated_at = datetime.now(UTC)
        return record

    def delete_project(self, project_id: UUID) -> bool:
        """Delete a project and, by cascade, all of its tasks."""
        if self._projects.pop(project_id, None) is None:
            return False
        self._tasks = {
            task_id: task
            for task_id, task in self._tasks.items()
            if task.project_id != project_id
        }
        return True

    # --- tasks ---
    # Every task lookup is scoped by project_id: a task found under the wrong
    # project is treated exactly like a missing one.
    # The caller is responsible for checking the project exists first.

    def create_task(self, project_id: UUID, data: TaskCreate) -> TaskRecord:
        now = datetime.now(UTC)
        record = TaskRecord(
            id=uuid4(),
            project_id=project_id,
            title=data.title,
            description=data.description,
            status=data.status,
            created_at=now,
            updated_at=now,
        )
        self._tasks[record.id] = record
        return record

    def list_tasks(self, project_id: UUID) -> list[TaskRecord]:
        return [t for t in self._tasks.values() if t.project_id == project_id]

    def get_task(self, project_id: UUID, task_id: UUID) -> TaskRecord | None:
        record = self._tasks.get(task_id)
        if record is None or record.project_id != project_id:
            return None
        return record

    def update_task(
        self, project_id: UUID, task_id: UUID, data: TaskUpdate
    ) -> TaskRecord | None:
        record = self.get_task(project_id, task_id)
        if record is None:
            return None
        record.title = data.title
        record.description = data.description
        record.status = data.status
        record.updated_at = datetime.now(UTC)
        return record

    def delete_task(self, project_id: UUID, task_id: UUID) -> bool:
        if self.get_task(project_id, task_id) is None:
            return False
        del self._tasks[task_id]
        return True
