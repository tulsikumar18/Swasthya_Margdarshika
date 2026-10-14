import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.ml.model_loader import model_registry

@pytest.fixture(scope="session", autouse=True)
def init_model():
    """Ensure the ML model and datasets are loaded for the test session."""
    model_registry.load_all()

@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    with TestClient(app) as test_client:
        yield test_client
