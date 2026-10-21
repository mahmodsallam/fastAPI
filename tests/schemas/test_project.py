import pytest
from pydantic import ValidationError

from app.schemas import ProjectCreate, ProjectUpdate


def test_project_create_accepts_minimal_payload() -> None:
    project = ProjectCreate(name="Atlas")

    assert project.name == "Atlas"
    assert project.description is None


def test_project_name_is_stripped() -> None:
    assert ProjectCreate(name="  Atlas  ").name == "Atlas"


@pytest.mark.parametrize("name", ["", "   "])
def test_project_name_rejects_blank(name: str) -> None:
    with pytest.raises(ValidationError):
        ProjectCreate(name=name)


def test_project_name_length_bounds() -> None:
    assert ProjectCreate(name="a" * 120)
    with pytest.raises(ValidationError):
        ProjectCreate(name="a" * 121)


def test_project_description_length_bound() -> None:
    assert ProjectCreate(name="x", description="d" * 2000)
    with pytest.raises(ValidationError):
        ProjectCreate(name="x", description="d" * 2001)


def test_project_rejects_unknown_fields() -> None:
    with pytest.raises(ValidationError):
        ProjectCreate.model_validate({"name": "x", "nmae": "typo"})


def test_project_update_has_same_rules_as_create() -> None:
    with pytest.raises(ValidationError):
        ProjectUpdate(name="")
