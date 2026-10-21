from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from app.repository import InMemoryStore

PROJECTS = "/api/v1/projects"


def make_project(client: TestClient, name: str) -> str:
    return client.post(PROJECTS, json={"name": name}).json()["id"]


def make_task(client: TestClient, project_id: str, title: str) -> dict:
    return client.post(f"{PROJECTS}/{project_id}/tasks", json={"title": title}).json()


def test_deleting_project_removes_its_tasks(
    client: TestClient, store: InMemoryStore
) -> None:
    project_id = make_project(client, "doomed")
    task = make_task(client, project_id, "t1")
    make_task(client, project_id, "t2")

    assert client.delete(f"{PROJECTS}/{project_id}").status_code == 204

    # Not reachable through the API...
    response = client.get(f"{PROJECTS}/{project_id}/tasks/{task['id']}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "project_not_found"
    # ...and not left behind in storage either.
    assert store.list_tasks(UUID(project_id)) == []
    assert store.get_task(UUID(project_id), UUID(task["id"])) is None


def test_deleting_project_keeps_other_projects_tasks(client: TestClient) -> None:
    doomed = make_project(client, "doomed")
    survivor = make_project(client, "survivor")
    make_task(client, doomed, "gone")
    kept = make_task(client, survivor, "kept")

    client.delete(f"{PROJECTS}/{doomed}")

    response = client.get(f"{PROJECTS}/{survivor}/tasks")
    assert response.status_code == 200
    assert response.json() == [kept]


def test_deleting_project_without_tasks_still_works(client: TestClient) -> None:
    project_id = make_project(client, "empty")

    assert client.delete(f"{PROJECTS}/{project_id}").status_code == 204


def test_unknown_project_delete_does_not_touch_tasks(client: TestClient) -> None:
    project_id = make_project(client, "real")
    task = make_task(client, project_id, "t")

    assert client.delete(f"{PROJECTS}/{uuid4()}").status_code == 404

    assert client.get(f"{PROJECTS}/{project_id}/tasks").json() == [task]
