import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.google_calendar import get_calendar_service


@pytest.fixture
def client():
    """Create a FastAPI TestClient."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_calendar_mock(monkeypatch):
    """Ensure in-memory mock mode and clean state for tests without external network dependencies."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "ENVIRONMENT", "test")
    monkeypatch.setattr(settings, "VAPI_SECRET_TOKEN", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    service = get_calendar_service()
    service._client = None
    service.clear_mock_events()
    yield
    service.clear_mock_events()
