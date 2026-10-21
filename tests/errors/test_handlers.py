from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.errors import AppError, register_exception_handlers
from app.main import app as real_app
from app.schemas import ProjectCreate


def build_test_app() -> FastAPI:
    """Small app with routes that trigger each error path."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/app-error")
    def app_error() -> None:
        raise AppError(404, "project_not_found", "Project not found")

    @app.get("/app-error-details")
    def app_error_details() -> None:
        raise AppError(409, "conflict", "Conflict", details={"hint": "retry"})

    @app.post("/validate")
    def validate(body: ProjectCreate) -> ProjectCreate:
        return body

    @app.get("/items/{item_id}")
    def item(item_id: int) -> int:
        return item_id

    @app.get("/boom")
    def boom() -> None:
        raise RuntimeError("secret internal detail")

    return app


client = TestClient(build_test_app(), raise_server_exceptions=False)


def test_app_error_uses_envelope() -> None:
    response = client.get("/app-error")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "project_not_found",
            "message": "Project not found",
            "details": None,
        }
    }


def test_app_error_carries_details() -> None:
    response = client.get("/app-error-details")

    assert response.status_code == 409
    assert response.json()["error"]["details"] == {"hint": "retry"}


def test_body_validation_error_uses_envelope() -> None:
    response = client.post("/validate", json={"name": ""})

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["message"] == "Request validation failed"
    assert [d["field"] for d in error["details"]] == ["body.name"]
    assert set(error["details"][0]) == {"field", "message", "type"}


def test_unknown_body_field_is_reported() -> None:
    response = client.post("/validate", json={"name": "ok", "extra": 1})

    assert response.status_code == 422
    fields = [d["field"] for d in response.json()["error"]["details"]]
    assert fields == ["body.extra"]


def test_path_validation_error_uses_envelope() -> None:
    response = client.get("/items/not-a-number")

    assert response.status_code == 422
    fields = [d["field"] for d in response.json()["error"]["details"]]
    assert fields == ["path.item_id"]


def test_validation_error_does_not_echo_input() -> None:
    response = client.post("/validate", json={"name": "", "description": "x" * 5000})

    assert "xxxxx" not in response.text


def test_unknown_route_uses_envelope() -> None:
    response = client.get("/nope")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_wrong_method_uses_envelope() -> None:
    response = client.delete("/validate")

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_unhandled_exception_hides_internals() -> None:
    response = client.get("/boom")

    assert response.status_code == 500
    assert response.json() == {
        "error": {
            "code": "internal_error",
            "message": "Internal server error",
            "details": None,
        }
    }
    assert "secret" not in response.text


def test_real_app_registers_handlers() -> None:
    response = TestClient(real_app).get("/api/v1/does-not-exist")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
