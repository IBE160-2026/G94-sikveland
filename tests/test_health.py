from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_health_returns_ok(settings: Settings) -> None:
    client = TestClient(create_app(settings))

    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_module_app_serves_health() -> None:
    """The object uvicorn loads (`app.main:app`) starts with defaults and no key."""
    from app.main import app

    response = TestClient(app).get("/api/health")

    assert response.json() == {"status": "ok"}
    assert app.state.settings.anthropic_api_key is None
