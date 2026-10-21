from functools import lru_cache

from app.repository import InMemoryStore


@lru_cache
def get_store() -> InMemoryStore:
    """One store per process. Tests swap it via app.dependency_overrides."""
    return InMemoryStore()
