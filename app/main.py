"""App wiring and startup. Start with `uv run uvicorn app.main:app`."""

from fastapi import FastAPI

from app.config import Settings, get_settings
from app.web import health


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings; uvicorn uses `.env`."""
    app = FastAPI(title="Norway Visa Guide For Thai")
    app.state.settings = settings if settings is not None else get_settings()
    app.include_router(health.router)
    return app


app = create_app()
