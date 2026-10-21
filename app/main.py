from fastapi import APIRouter, FastAPI

from app.errors import register_exception_handlers

API_PREFIX = "/api/v1"

app = FastAPI(title="Atlas", version="0.1.0")
register_exception_handlers(app)

api_router = APIRouter(prefix=API_PREFIX)


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
