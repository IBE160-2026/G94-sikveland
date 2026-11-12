"""App wiring and startup. Start with `uv run uvicorn app.main:app`."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.adapters.file_content import load_content
from app.config import ROOT, Settings, get_settings
from app.web import health, texts

CONTENT_FILE = ROOT / "content" / "texts.yaml"
STATIC_DIR = ROOT / "app" / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    """Build the app. Tests pass their own settings; uvicorn uses `.env`.

    Raises `ContentError` if `content/texts.yaml` is invalid, so the app never
    starts with missing or broken fixed texts.
    """
    settings = settings if settings is not None else get_settings()
    app = FastAPI(title="Norway Visa Guide For Thai")
    app.state.settings = settings
    app.state.content = load_content(CONTENT_FILE, settings.adviser_contact)
    app.include_router(health.router)
    app.include_router(texts.router)
    # Mounted last so every /api/* route is matched before the static files.
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
    return app


app = create_app()
