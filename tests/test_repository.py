from uuid import uuid4

from app.repository import InMemoryStore
from app.schemas import ProjectCreate, ProjectUpdate


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
