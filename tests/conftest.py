import os

import pytest

from app.config import Settings, get_settings

# Runs before any test module is imported, so importing `app.main` (which
# builds the app at import time) never reads a local `.env` or a real API key.
Settings.model_config["env_file"] = None
for _name in Settings.model_fields:
    os.environ.pop(_name.upper(), None)
get_settings.cache_clear()


@pytest.fixture
def settings() -> Settings:
    """Default settings, ignoring any local `.env` file."""
    return Settings(_env_file=None)
