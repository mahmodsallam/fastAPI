import pytest
from fastapi.testclient import TestClient

from app.main import app

P = "/api/v1/projects"
T = "/api/v1/projects/{project_id}/tasks"

# (method, path) -> status codes the docs must declare for that operation
EXPECTED: dict[tuple[str, str], set[str]] = {
    ("get", "/api/v1/health"): {"200"},
    ("post", P): {"201", "422"},
    ("get", P): {"200"},
    ("get", P + "/{project_id}"): {"200", "404", "422"},
    ("put", P + "/{project_id}"): {"200", "404", "422"},
    ("delete", P + "/{project_id}"): {"204", "404", "422"},
    ("post", T): {"201", "404", "422"},
    ("get", T): {"200", "404", "422"},
    ("get", T + "/{task_id}"): {"200", "404", "422"},
    ("put", T + "/{task_id}"): {"200", "404", "422"},
    ("delete", T + "/{task_id}"): {"204", "404", "422"},
}


@pytest.fixture(scope="module")
def spec() -> dict:
    return TestClient(app).get("/openapi.json").json()


def test_openapi_documents_exactly_the_expected_operations(spec: dict) -> None:
    documented = {
        (method, path) for path, ops in spec["paths"].items() for method in ops
    }

    assert documented == set(EXPECTED)


@pytest.mark.parametrize(("method", "path"), sorted(EXPECTED))
def test_operation_declares_expected_status_codes(
    spec: dict, method: str, path: str
) -> None:
    operation = spec["paths"][path][method]

    assert set(operation["responses"]) == EXPECTED[(method, path)]


@pytest.mark.parametrize(("method", "path"), sorted(EXPECTED))
def test_error_responses_use_the_error_envelope_model(
    spec: dict, method: str, path: str
) -> None:
    responses = spec["paths"][path][method]["responses"]

    for status, response in responses.items():
        if status in {"404", "422"}:
            schema = response["content"]["application/json"]["schema"]
            assert schema["$ref"].endswith("/ErrorResponse")


def test_default_validation_error_schema_is_gone(spec: dict) -> None:
    schemas = spec["components"]["schemas"]

    assert "ErrorResponse" in schemas
    assert "HTTPValidationError" not in schemas
    assert "ValidationError" not in schemas


@pytest.mark.parametrize(("method", "path"), sorted(EXPECTED))
def test_operation_has_summary_and_description(
    spec: dict, method: str, path: str
) -> None:
    operation = spec["paths"][path][method]

    assert operation["summary"]
    assert operation["description"]


def test_204_responses_have_no_body(spec: dict) -> None:
    for (method, path), statuses in EXPECTED.items():
        if "204" in statuses:
            assert "content" not in spec["paths"][path][method]["responses"]["204"]


def test_put_descriptions_state_full_replacement(spec: dict) -> None:
    for path in (P + "/{project_id}", T + "/{task_id}"):
        assert "replac" in spec["paths"][path]["put"]["description"].lower()


def test_app_has_description_and_tag_descriptions(spec: dict) -> None:
    assert spec["info"]["description"]
    tags = {tag["name"]: tag.get("description") for tag in spec["tags"]}
    assert set(tags) == {"health", "projects", "tasks"}
    assert all(tags.values())
