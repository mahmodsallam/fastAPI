from uuid import uuid4

from app.repository import InMemoryStore
from app.schemas import (
    ProjectCreate,
    ProjectUpdate,
    TaskCreate,
    TaskStatus,
    TaskUpdate,
)


def test_create_assigns_id_and_equal_timestamps() -> None:
    store = InMemoryStore()

    record = store.create_project(ProjectCreate(name="Atlas", description="d"))

    assert record.name == "Atlas"
    assert record.description == "d"
    assert record.created_at == record.updated_at
    assert record.created_at.tzinfo is not None


def test_get_returns_none_for_unknown_id() -> None:
    assert InMemoryStore().get_project(uuid4()) is None


def test_list_preserves_creation_order() -> None:
    store = InMemoryStore()
    names = ["a", "b", "c"]
    for name in names:
        store.create_project(ProjectCreate(name=name))

    assert [p.name for p in store.list_projects()] == names


def test_update_replaces_fields_and_bumps_updated_at() -> None:
    store = InMemoryStore()
    created = store.create_project(ProjectCreate(name="old", description="d"))

    updated = store.update_project(created.id, ProjectUpdate(name="new"))

    assert updated is not None
    assert updated.name == "new"
    assert updated.description is None
    assert updated.created_at == created.created_at
    assert updated.updated_at > created.created_at


def test_update_unknown_returns_none() -> None:
    assert InMemoryStore().update_project(uuid4(), ProjectUpdate(name="x")) is None


def test_delete_returns_whether_row_existed() -> None:
    store = InMemoryStore()
    record = store.create_project(ProjectCreate(name="x"))

    assert store.delete_project(record.id) is True
    assert store.delete_project(record.id) is False
    assert store.get_project(record.id) is None


# --- tasks ---


def test_task_lookup_is_scoped_by_project() -> None:
    store = InMemoryStore()
    project_a, project_b = uuid4(), uuid4()
    task = store.create_task(project_a, TaskCreate(title="t"))

    assert store.get_task(project_a, task.id) is task
    assert store.get_task(project_b, task.id) is None
    assert store.update_task(project_b, task.id, TaskUpdate(title="x")) is None
    assert store.delete_task(project_b, task.id) is False
    assert store.get_task(project_a, task.id) is task


def test_list_tasks_filters_by_project_and_keeps_order() -> None:
    store = InMemoryStore()
    project_a, project_b = uuid4(), uuid4()
    store.create_task(project_a, TaskCreate(title="a1"))
    store.create_task(project_b, TaskCreate(title="b1"))
    store.create_task(project_a, TaskCreate(title="a2"))

    assert [t.title for t in store.list_tasks(project_a)] == ["a1", "a2"]


def test_update_task_replaces_fields_and_keeps_project() -> None:
    store = InMemoryStore()
    project_id = uuid4()
    created = store.create_task(
        project_id, TaskCreate(title="old", description="d", status="done")
    )

    updated = store.update_task(project_id, created.id, TaskUpdate(title="new"))

    assert updated is not None
    assert (updated.title, updated.description) == ("new", None)
    assert updated.status is TaskStatus.TODO
    assert updated.project_id == project_id
    assert updated.updated_at > created.created_at


def test_delete_project_removes_only_its_tasks() -> None:
    store = InMemoryStore()
    doomed = store.create_project(ProjectCreate(name="doomed"))
    survivor = store.create_project(ProjectCreate(name="survivor"))
    store.create_task(doomed.id, TaskCreate(title="gone"))
    kept = store.create_task(survivor.id, TaskCreate(title="kept"))

    store.delete_project(doomed.id)

    assert store.list_tasks(doomed.id) == []
    assert store.list_tasks(survivor.id) == [kept]
