import pytest
from pydantic import ValidationError

from app.schemas import TaskCreate, TaskStatus, TaskUpdate


def test_task_status_defaults_to_todo() -> None:
    assert TaskCreate(title="Write tests").status is TaskStatus.TODO


def test_task_status_accepts_known_values() -> None:
    assert TaskCreate(title="t", status="in_progress").status is TaskStatus.IN_PROGRESS


def test_task_status_rejects_unknown_value() -> None:
    with pytest.raises(ValidationError):
        TaskCreate.model_validate({"title": "t", "status": "blocked"})


def test_task_title_rules() -> None:
    assert TaskCreate(title="  trim me ").title == "trim me"
    assert TaskCreate(title="a" * 200)
    with pytest.raises(ValidationError):
        TaskCreate(title="a" * 201)
    with pytest.raises(ValidationError):
        TaskCreate(title="   ")


def test_task_description_length_bound() -> None:
    assert TaskCreate(title="t", description="d" * 2000)
    with pytest.raises(ValidationError):
        TaskCreate(title="t", description="d" * 2001)


def test_task_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        TaskCreate.model_validate({"title": "t", "project_id": "nope"})


def test_task_update_has_same_rules_as_create() -> None:
    with pytest.raises(ValidationError):
        TaskUpdate.model_validate({"title": "t", "status": "bad"})
