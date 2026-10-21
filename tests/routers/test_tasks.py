from datetime import datetime
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

PROJECTS = "/api/v1/projects"


def make_project(client: TestClient, name: str = "Atlas") -> str:
    response = client.post(PROJECTS, json={"name": name})
    assert response.status_code == 201
    return response.json()["id"]


def tasks_url(project_id: str | UUID) -> str:
    return f"{PROJECTS}/{project_id}/tasks"


def make_task(client: TestClient, project_id: str, **payload: object) -> dict:
    response = client.post(tasks_url(project_id), json={"title": "Write", **payload})
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def project_id(client: TestClient) -> str:
    return make_project(client)


# --- create ---


def test_create_returns_201_and_read_model(
    client: TestClient, project_id: str
) -> None:
    response = client.post(
        tasks_url(project_id),
        json={"title": "Write tests", "description": "All of them", "status": "done"},
    )

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {
        "id",
        "project_id",
        "title",
        "description",
        "status",
        "created_at",
        "updated_at",
    }
    assert body["project_id"] == project_id
    assert body["title"] == "Write tests"
    assert body["description"] == "All of them"
    assert body["status"] == "done"
    assert body["created_at"] == body["updated_at"]
    UUID(body["id"])
    assert datetime.fromisoformat(body["created_at"]).tzinfo is not None


def test_create_defaults_status_to_todo(client: TestClient, project_id: str) -> None:
    task = make_task(client, project_id)

    assert task["status"] == "todo"
    assert task["description"] is None


def test_create_trims_title(client: TestClient, project_id: str) -> None:
    assert make_task(client, project_id, title="  Write  ")["title"] == "Write"


@pytest.mark.parametrize(
    ("payload", "field"),
    [
        ({}, "body.title"),
        ({"title": ""}, "body.title"),
        ({"title": "   "}, "body.title"),
        ({"title": "a" * 201}, "body.title"),
        ({"title": "ok", "status": "blocked"}, "body.status"),
        ({"title": "ok", "description": "d" * 2001}, "body.description"),
        ({"title": "ok", "project_id": str(uuid4())}, "body.project_id"),
    ],
)
def test_create_rejects_invalid_payload(
    client: TestClient, project_id: str, payload: dict, field: str
) -> None:
    response = client.post(tasks_url(project_id), json=payload)

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert field in [d["field"] for d in error["details"]]
    assert client.get(tasks_url(project_id)).json() == []


# --- list ---


def test_list_empty(client: TestClient, project_id: str) -> None:
    response = client.get(tasks_url(project_id))

    assert response.status_code == 200
    assert response.json() == []


def test_list_returns_tasks_in_creation_order(
    client: TestClient, project_id: str
) -> None:
    for title in ["first", "second", "third"]:
        make_task(client, project_id, title=title)

    response = client.get(tasks_url(project_id))

    assert response.status_code == 200
    assert [t["title"] for t in response.json()] == ["first", "second", "third"]


def test_list_only_returns_tasks_of_that_project(client: TestClient) -> None:
    project_a = make_project(client, "A")
    project_b = make_project(client, "B")
    make_task(client, project_a, title="in A")
    make_task(client, project_b, title="in B")

    titles = [t["title"] for t in client.get(tasks_url(project_a)).json()]

    assert titles == ["in A"]


# --- get ---


def test_get_returns_task(client: TestClient, project_id: str) -> None:
    created = make_task(client, project_id)

    response = client.get(f"{tasks_url(project_id)}/{created['id']}")

    assert response.status_code == 200
    assert response.json() == created


def test_get_unknown_task_returns_404_envelope(
    client: TestClient, project_id: str
) -> None:
    response = client.get(f"{tasks_url(project_id)}/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "task_not_found",
            "message": "Task not found",
            "details": None,
        }
    }


def test_get_task_under_wrong_project_returns_404(client: TestClient) -> None:
    project_a = make_project(client, "A")
    project_b = make_project(client, "B")
    task = make_task(client, project_a)

    response = client.get(f"{tasks_url(project_b)}/{task['id']}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_get_with_malformed_task_id_returns_422(
    client: TestClient, project_id: str
) -> None:
    response = client.get(f"{tasks_url(project_id)}/not-a-uuid")

    assert response.status_code == 422
    fields = [d["field"] for d in response.json()["error"]["details"]]
    assert fields == ["path.task_id"]


# --- update ---


def test_put_replaces_fields_and_bumps_updated_at(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id, description="old", status="todo")

    response = client.put(
        f"{tasks_url(project_id)}/{created['id']}",
        json={"title": "Renamed", "status": "in_progress"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["project_id"] == project_id
    assert body["title"] == "Renamed"
    assert body["status"] == "in_progress"
    assert body["description"] is None  # full replacement: omitted -> null
    assert body["created_at"] == created["created_at"]
    assert body["updated_at"] > created["updated_at"]
    assert client.get(f"{tasks_url(project_id)}/{created['id']}").json() == body


def test_put_omitted_status_resets_to_todo(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id, status="done")

    response = client.put(
        f"{tasks_url(project_id)}/{created['id']}", json={"title": "x"}
    )

    assert response.json()["status"] == "todo"


def test_put_unknown_task_returns_404(client: TestClient, project_id: str) -> None:
    response = client.put(f"{tasks_url(project_id)}/{uuid4()}", json={"title": "x"})

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_put_task_under_wrong_project_returns_404_and_keeps_data(
    client: TestClient,
) -> None:
    project_a = make_project(client, "A")
    project_b = make_project(client, "B")
    task = make_task(client, project_a, title="original")

    response = client.put(
        f"{tasks_url(project_b)}/{task['id']}", json={"title": "hijacked"}
    )

    assert response.status_code == 404
    assert client.get(f"{tasks_url(project_a)}/{task['id']}").json() == task


def test_put_invalid_payload_returns_422_and_keeps_data(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id)

    response = client.put(
        f"{tasks_url(project_id)}/{created['id']}", json={"title": ""}
    )

    assert response.status_code == 422
    assert client.get(f"{tasks_url(project_id)}/{created['id']}").json() == created


def test_put_cannot_move_task_to_another_project(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id)

    response = client.put(
        f"{tasks_url(project_id)}/{created['id']}",
        json={"title": "x", "project_id": str(uuid4())},
    )

    assert response.status_code == 422


# --- delete ---


def test_delete_returns_204_and_removes_task(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id)

    response = client.delete(f"{tasks_url(project_id)}/{created['id']}")

    assert response.status_code == 204
    assert response.content == b""
    assert client.get(f"{tasks_url(project_id)}/{created['id']}").status_code == 404
    assert client.get(tasks_url(project_id)).json() == []


def test_delete_unknown_task_returns_404(client: TestClient, project_id: str) -> None:
    response = client.delete(f"{tasks_url(project_id)}/{uuid4()}")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "task_not_found"


def test_delete_task_under_wrong_project_returns_404_and_keeps_task(
    client: TestClient,
) -> None:
    project_a = make_project(client, "A")
    project_b = make_project(client, "B")
    task = make_task(client, project_a)

    response = client.delete(f"{tasks_url(project_b)}/{task['id']}")

    assert response.status_code == 404
    assert client.get(f"{tasks_url(project_a)}/{task['id']}").status_code == 200


def test_delete_twice_returns_404_the_second_time(
    client: TestClient, project_id: str
) -> None:
    created = make_task(client, project_id)
    client.delete(f"{tasks_url(project_id)}/{created['id']}")

    assert client.delete(f"{tasks_url(project_id)}/{created['id']}").status_code == 404


def test_deleting_a_task_leaves_siblings(client: TestClient, project_id: str) -> None:
    keep = make_task(client, project_id, title="keep")
    drop = make_task(client, project_id, title="drop")

    client.delete(f"{tasks_url(project_id)}/{drop['id']}")

    assert client.get(tasks_url(project_id)).json() == [keep]


# --- missing project: every task route ---


@pytest.mark.parametrize(
    ("method", "suffix", "body"),
    [
        ("post", "", {"title": "x"}),
        ("get", "", None),
        ("get", f"/{uuid4()}", None),
        ("put", f"/{uuid4()}", {"title": "x"}),
        ("delete", f"/{uuid4()}", None),
    ],
)
def test_missing_project_returns_404_on_every_task_route(
    client: TestClient, method: str, suffix: str, body: dict | None
) -> None:
    response = client.request(method, tasks_url(uuid4()) + suffix, json=body)

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"


def test_malformed_project_id_returns_422(client: TestClient) -> None:
    response = client.get(tasks_url("not-a-uuid"))

    assert response.status_code == 422
    fields = [d["field"] for d in response.json()["error"]["details"]]
    assert fields == ["path.project_id"]
