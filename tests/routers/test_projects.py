from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

BASE = "/api/v1/projects"


def create(client: TestClient, **payload: object) -> dict:
    response = client.post(BASE, json={"name": "Atlas", **payload})
    assert response.status_code == 201
    return response.json()


# --- create ---


def test_create_returns_201_and_read_model(client: TestClient) -> None:
    response = client.post(BASE, json={"name": "Atlas", "description": "Docs"})

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"id", "name", "description", "created_at", "updated_at"}
    assert body["name"] == "Atlas"
    assert body["description"] == "Docs"
    assert body["created_at"] == body["updated_at"]
    UUID(body["id"])
    assert datetime.fromisoformat(body["created_at"]).tzinfo is not None


def test_create_without_description_defaults_to_null(client: TestClient) -> None:
    assert create(client)["description"] is None


def test_create_trims_name(client: TestClient) -> None:
    assert create(client, name="  Atlas  ")["name"] == "Atlas"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "body.name"),
        ({"name": ""}, "body.name"),
        ({"name": "   "}, "body.name"),
        ({"name": "a" * 121}, "body.name"),
        ({"name": 5}, "body.name"),
        ({"name": "ok", "description": "d" * 2001}, "body.description"),
        ({"name": "ok", "owner": "me"}, "body.owner"),
    ],
)
def test_create_rejects_invalid_payload(
    client: TestClient, payload: dict, field: str
) -> None:
    response = client.post(BASE, json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert field in [d["field"] for d in error["details"]]
    assert client.get(BASE).json() == []


# --- list ---


def test_list_empty(client: TestClient) -> None:
    response = client.get(BASE)

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_projects_in_creation_order(client: TestClient) -> None:
    for name in ["first", "second", "third"]:
        create(client, name=name)

    response = client.get(BASE)

    assert response.status_code == 200
    assert [p["name"] for p in response.json()] == ["first", "second", "third"]


# --- get ---


def test_get_returns_project(client: TestClient) -> None:
    created = create(client)

    response = client.get(f"{BASE}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_project_returns_404_envelope(client: TestClient) -> None:
    response = client.get(f"{BASE}/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "project_not_found",
            "message": "Project not found",
            "details": None,
        }
    }


def test_get_with_malformed_id_returns_422(client: TestClient) -> None:
    response = client.get(f"{BASE}/not-a-uuid")

    assert response.status_code == 422
    fields = [d["field"] for d in response.json()["error"]["details"]]
    assert fields == ["path.project_id"]


# --- update ---


def test_put_replaces_fields_and_bumps_updated_at(client: TestClient) -> None:
    created = create(client, description="old")

    response = client.put(f"{BASE}/{created['id']}", json={"name": "Renamed"})

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["name"] == "Renamed"
    assert body["description"] is None  # full replacement: omitted -> null
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > created["updated_at"]
    assert client.get(f"{BASE}/{created['id']}").json() == body


def test_put_unknown_project_returns_404(client: TestClient) -> None:
    response = client.put(f"{BASE}/{uuid4()}", json={"name": "x"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_put_invalid_payload_returns_422_and_keeps_data(client: TestClient) -> None:
    created = create(client)

    response = client.put(f"{BASE}/{created['id']}", json={"name": ""})

    assert response.status_code == 422
    assert client.get(f"{BASE}/{created['id']}").json() == created


def test_put_rejects_server_managed_fields(client: TestClient) -> None:
    created = create(client)

    response = client.put(
        f"{BASE}/{created['id']}", json={"name": "x", "id": str(uuid4())}
    )

    assert response.status_code == 422


# --- delete ---


def test_delete_returns_204_and_removes_project(client: TestClient) -> None:
    created = create(client)

    response = client.delete(f"{BASE}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{BASE}/{created['id']}").status_code == 404
    assert client.get(BASE).json() == []


def test_delete_unknown_project_returns_404(client: TestClient) -> None:
    response = client.delete(f"{BASE}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_delete_twice_returns_404_the_second_time(client: TestClient) -> None:
    created = create(client)
    client.delete(f"{BASE}/{created['id']}")

    assert client.delete(f"{BASE}/{created['id']}").status_code == 404


# --- isolation ---


def test_each_test_starts_with_empty_store(client: TestClient) -> None:
    assert client.get(BASE).json() == []
    create(client)


def test_store_is_not_shared_with_previous_test(client: TestClient) -> None:
    assert client.get(BASE).json() == []
