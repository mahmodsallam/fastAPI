from fastapi import APIRouter, FastAPI

from app.errors import register_exception_handlers
from app.routers import projects, tasks

API_PREFIX = "/api/v1"

DESCRIPTION = """
Atlas is a project and task management API.

**Milestone 1:** data is held in memory and is lost when the server restarts.
There is no authentication yet.

Every error response uses one envelope:
`{"error": {"code": "...", "message": "...", "details": ...}}`.
"""

TAGS_METADATA = [
    {"name": "health", "description": "Liveness check."},
    {"name": "projects", "description": "Create, read, replace and delete projects."},
    {
        "name": "tasks",
        "description": "Tasks always belong to exactly one project and are "
        "addressed through it.",
    },
]

app = FastAPI(
    title="Atlas",
    version="0.1.0",
    description=DESCRIPTION,
    openapi_tags=TAGS_METADATA,
)
register_exception_handlers(app)

api_router = APIRouter(prefix=API_PREFIX)


@api_router.get("/health", tags=["health"], summary="Health check")
def health() -> dict[str, str]:
    """Return `{"status": "ok"}` while the service is running."""
    return {"status": "ok"}


api_router.include_router(projects.router)
api_router.include_router(tasks.router)

app.include_router(api_router)
