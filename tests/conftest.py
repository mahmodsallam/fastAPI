from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_store
from app.main import app
from app.repository import InMemoryStore


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture
def client(store: InMemoryStore) -> Iterator[TestClient]:
    """TestClient wired to a fresh store, so tests never share state."""
    app.dependency_overrides[get_store] = lambda: store
    yield TestClient(app)
    app.dependency_overrides.clear()
