import os
from pathlib import Path

import pytest

from app.config import Settings, get_settings

# Runs before any test module is imported, so importing `app.main` (which
# builds the app at import time) never reads a local `.env` or a real API key.
Settings.model_config["env_file"] = None
for _name in Settings.model_fields:
    os.environ.pop(_name.upper(), None)
# Credentials and endpoint the Anthropic SDK reads on its own, besides ANTHROPIC_API_KEY.
for _name in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL", "ANTHROPIC_PROFILE"):
    os.environ.pop(_name, None)
get_settings.cache_clear()


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    """Default settings, ignoring any local `.env` file; the request log goes to `tmp_path`."""
    return Settings(_env_file=None, request_log_path=str(tmp_path / "requests.jsonl"))
