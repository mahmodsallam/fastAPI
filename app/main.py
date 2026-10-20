from fastapi import APIRouter, FastAPI

API_PREFIX = "/api/v1"

app = FastAPI(title="Atlas", version="0.1.0")

api_router = APIRouter(prefix=API_PREFIX)


@api_router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(api_router)
