# Atlas

Atlas is a project and task management REST API built with **FastAPI** and **Pydantic v2**. It is the backend foundation of a larger knowledge-and-workflow platform; the full scope is in [`.claude/PRD.md`](.claude/PRD.md).

> **Current status: Milestone 1.** Data is stored **in memory** and is **lost when the server restarts**. There is **no database and no authentication yet**. PostgreSQL arrives in Milestone 2 and JWT auth in Milestone 3.

## Contents

- [Quick start](#quick-start)
- [API reference](#api-reference)
- [Project structure](#project-structure)
- [How a request flows](#how-a-request-flows)
- [Tests](#tests)
- [Design decisions](#design-decisions)
- [Known limitations](#known-limitations)
- [Roadmap](#roadmap)

## Quick start

Requires Python 3.12+.

```bash
# from the repository root, with your virtual environment active
pip install fastapi uvicorn          # runtime
pip install pytest httpx             # tests

uvicorn app.main:app --reload        # start the API on http://127.0.0.1:8000
python -m pytest                     # run the test suite
```

Once the server is running:

| URL | What it is |
|---|---|
| <http://127.0.0.1:8000/docs> | Interactive Swagger UI |
| <http://127.0.0.1:8000/redoc> | ReDoc documentation |
| <http://127.0.0.1:8000/openapi.json> | Raw OpenAPI document |
| <http://127.0.0.1:8000/api/v1/health> | Health check |

Try it:

```bash
# create a project
curl -X POST localhost:8000/api/v1/projects \
  -H 'content-type: application/json' \
  -d '{"name": "Website redesign", "description": "Q4 work"}'

# create a task in it (use the "id" returned above)
curl -X POST localhost:8000/api/v1/projects/<project_id>/tasks \
  -H 'content-type: application/json' \
  -d '{"title": "Draft wireframes", "status": "in_progress"}'
```

## API reference

All routes are under the `/api/v1` prefix. Identifiers are UUIDs. Timestamps are UTC, ISO 8601.

### Routes

| Method | Endpoint | Purpose | Success |
|---|---|---|---|
| `GET` | `/health` | Liveness check | 200 |
| `POST` | `/projects` | Create a project | 201 |
| `GET` | `/projects` | List projects (oldest first) | 200 |
| `GET` | `/projects/{project_id}` | Get a project | 200 |
| `PUT` | `/projects/{project_id}` | Replace a project's editable fields | 200 |
| `DELETE` | `/projects/{project_id}` | Delete a project **and its tasks** | 204 |
| `POST` | `/projects/{project_id}/tasks` | Create a task | 201 |
| `GET` | `/projects/{project_id}/tasks` | List a project's tasks (oldest first) | 200 |
| `GET` | `/projects/{project_id}/tasks/{task_id}` | Get a task | 200 |
| `PUT` | `/projects/{project_id}/tasks/{task_id}` | Replace a task's editable fields | 200 |
| `DELETE` | `/projects/{project_id}/tasks/{task_id}` | Delete a task | 204 |

### Request bodies

| Model | Field | Rules |
|---|---|---|
| Project (create / replace) | `name` | required, 1–120 characters after trimming |
| | `description` | optional, up to 2000 characters |
| Task (create / replace) | `title` | required, 1–200 characters after trimming |
| | `description` | optional, up to 2000 characters |
| | `status` | `todo` (default), `in_progress` or `done` |

- Surrounding whitespace is trimmed, so a name of `"   "` is rejected.
- **Unknown fields are rejected** (422), which catches typos. Clients cannot send `id`, `project_id`, `created_at` or `updated_at`; the server owns them.
- `PUT` is a **full replacement**, not a partial update. An omitted `description` becomes `null` and an omitted task `status` resets to `todo`. `id`, `created_at` and a task's `project_id` never change; `updated_at` is refreshed.

### Responses

A project looks like:

```json
{
  "id": "3d3217b1-783f-4009-a18f-cc4b88321d0c",
  "name": "Website redesign",
  "description": "Q4 work",
  "created_at": "2026-10-21T18:16:21.435809Z",
  "updated_at": "2026-10-21T18:16:21.435809Z"
}
```

A task is the same shape with `title` instead of `name`, plus `project_id` and `status`.

### Errors

Every non-2xx response uses one envelope:

```json
{ "error": { "code": "project_not_found", "message": "Project not found", "details": null } }
```

| Status | `code` | When |
|---|---|---|
| 404 | `project_not_found` | The project does not exist (on any project or task route) |
| 404 | `task_not_found` | The task does not exist, **or belongs to a different project** |
| 404 | `not_found` / 405 `method_not_allowed` | Unknown URL / wrong HTTP method |
| 422 | `validation_error` | Invalid body, or a malformed UUID in the path |
| 500 | `internal_error` | Unexpected failure (generic message, no internals exposed) |

For `422`, `details` lists each problem as `{ "field", "message", "type" }`, for example `"field": "body.name"` or `"field": "path.project_id"`. The submitted values are never echoed back.

A request is checked in this order: **path and body validation (422), then project (404), then task (404)**. So an invalid body sent to a non-existent project returns 422, not 404.

## Project structure

```
.
├── README.md
├── pyproject.toml              # dependencies and pytest configuration
├── .gitignore
├── .claude/
│   ├── CLAUDE.md               # how we collaborate on this project
│   └── PRD.md                  # product requirements and roadmap
├── app/                        # the application
│   ├── main.py                 # creates the FastAPI app and wires everything together
│   ├── repository.py           # in-memory storage (temporary, replaced in Milestone 2)
│   ├── dependencies.py         # get_store(): the dependency routers receive storage from
│   ├── schemas/                # Pydantic request/response models
│   │   ├── __init__.py         # re-exports the public names
│   │   ├── base.py             # StrictInput: trims strings, forbids unknown fields
│   │   ├── project.py          # ProjectCreate, ProjectUpdate, ProjectRead
│   │   └── task.py             # TaskStatus, TaskCreate, TaskUpdate, TaskRead
│   ├── errors/                 # the error envelope and its handlers
│   │   ├── __init__.py         # re-exports the public names
│   │   ├── exceptions.py       # AppError: raised by routers
│   │   ├── models.py           # ErrorResponse model + error_responses() helper for OpenAPI
│   │   └── handlers.py         # turns every error into the envelope; register_exception_handlers()
│   └── routers/                # HTTP layer: thin route functions
│       ├── projects.py         # the five /projects routes
│       └── tasks.py            # the five /projects/{id}/tasks routes
└── tests/                      # mirrors app/
    ├── conftest.py             # shared fixtures: a fresh store and client per test
    ├── test_health.py
    ├── test_repository.py      # the in-memory store on its own
    ├── test_openapi.py         # the generated docs match the real behavior
    ├── schemas/
    │   ├── test_project.py
    │   └── test_task.py
    ├── errors/
    │   └── test_handlers.py    # each error path produces the envelope
    └── routers/
        ├── test_projects.py
        ├── test_tasks.py
        └── test_project_deletion.py   # cascade delete and isolation between projects
```

### What each part is responsible for

- **`main.py`**: builds the `FastAPI` app, registers the error handlers, mounts the health route and both routers under `/api/v1`, and holds the OpenAPI description and tag metadata.
- **`routers/`**: the transport layer. Each function receives validated input, asks the store for data, and turns "not found" into an `AppError`. There is no business logic beyond that, and no service layer, since there are no rules complex enough to need one yet.
- **`schemas/`**: the API contract. `Create`/`Update` models validate input; `Read` models define output. They are separate from the stored records so internal fields can never leak into responses.
- **`repository.py`**: `InMemoryStore` holds two dicts (projects and tasks) and the `ProjectRecord` / `TaskRecord` dataclasses. It returns `None` or `False` for missing rows and leaves HTTP decisions to the routers. Task lookups are always scoped by `project_id`, and deleting a project removes its tasks.
- **`dependencies.py`**: `get_store()` returns one store per process. Routers receive it through `Depends(get_store)`, and tests replace it with a fresh store.
- **`errors/`**: `AppError` is raised by routers. Handlers convert `AppError`, framework errors (404/405), validation errors and unexpected exceptions into the single envelope.

## How a request flows

```
HTTP request
   │
   ▼
FastAPI route (routers/*.py)      path UUIDs + body validated against schemas/*  ──► 422 envelope on failure
   │  Depends(get_store)
   ▼
InMemoryStore (repository.py)     returns a record, None, or a bool
   │
   ▼
route: None/False → raise AppError  ──► errors/handlers.py ──► 404 envelope
   │
   ▼
response_model (…Read)            record → JSON, only the declared fields
```

## Tests

```bash
python -m pytest                          # everything
python -m pytest tests/routers            # one folder
python -m pytest tests/routers/test_tasks.py -k wrong_project   # one area
python -m pytest -v                       # list every test name
```

The tests are organized in layers, mirroring `app/`:

| Layer | Files | What it checks |
|---|---|---|
| Schemas (unit) | `tests/schemas/` | Length limits, whitespace trimming, default status, enum values, unknown fields rejected |
| Store (unit) | `tests/test_repository.py` | Create/get/list/update/delete, ordering, task scoping by project, cascade |
| Error handling | `tests/errors/test_handlers.py` | Every error path returns the envelope; the 500 hides internals; 422 details don't echo input |
| API (integration) | `tests/routers/` | All ten routes through HTTP: happy paths, invalid payloads, 404 for unknown/wrong-project resources, malformed UUIDs, full-replacement `PUT`, `DELETE` twice, cascade delete |
| Documentation | `tests/test_openapi.py` | The OpenAPI document lists exactly the real routes and status codes, uses the error model for 404/422, and has summaries and descriptions |

Each test gets a **fresh store** from the `client` fixture in `tests/conftest.py`, which overrides `get_store`. Tests never share data and the order they run in does not matter.

## Design decisions

These were agreed before implementation:

| Decision | Choice | Why |
|---|---|---|
| IDs | UUID4 | Stable and non-guessable; maps directly onto a Postgres `UUID` column later |
| Update style | `PUT` only (full replacement) | Matches the PRD; `PATCH` can be added later |
| Deleting a project with tasks | Cascade | Avoids orphans; the database will enforce it in Milestone 2 |
| Task in the wrong project | 404, same as missing | Does not reveal that a task exists elsewhere |
| Error format | Custom envelope on every error | One shape for clients to handle |
| Structure | Flat: thin routers + one store, no service layer | No business rules yet that justify extra layers |
| Strict input | Trim strings, forbid unknown fields | Catches client typos and blocks setting server-managed fields |

## Known limitations

- **In-memory data.** Restarting the server erases everything, and running several worker processes would give each its own separate data.
- **No authentication or authorization.** Anyone who can reach the API can use it.
- **No pagination, filtering or sorting.** Lists return everything, oldest first.
- **Not thread-safe by design.** The store is a plain scaffold for a single-user learning setup.

## Roadmap

| Milestone | Scope |
|---|---|
| **M1: API foundation** (this) | Projects and tasks CRUD, schemas, OpenAPI, in-memory store, tests |
| M2: Database | PostgreSQL, SQLAlchemy 2.x, Alembic migrations, Docker Compose |
| M3: Security | Registration/login, JWT, project membership and roles |
| M4: Production capabilities | Documents, pagination/filtering, logging |
| M5: Deployment and UI | Docker, CI, hosted deployment, minimal dashboard |
| M6: AI extension | Document ingestion, vector search, permission-aware RAG |

See [`.claude/PRD.md`](.claude/PRD.md) for the full requirements.
