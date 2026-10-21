from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas import ProjectCreate, ProjectUpdate


@dataclass
class ProjectRecord:
    id: UUID
    name: str
    description: str | None
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
        return self._projects.pop(project_id, None) is not None
