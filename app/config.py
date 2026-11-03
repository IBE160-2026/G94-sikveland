"""Settings, read from the environment and `.env` in the project root."""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent

Effort = Literal["low", "medium", "high", "xhigh", "max"]
# USD per million tokens.
Price = Annotated[float, Field(ge=0, allow_inf_nan=False)]


class Settings(BaseSettings):
    """All settings for the app. Env names are the field names in upper case."""

    model_config = SettingsConfigDict(
        env_file=ROOT / ".env",
        # utf-8-sig also reads files saved with a BOM (e.g. by PowerShell 5.1).
        env_file_encoding="utf-8-sig",
        env_ignore_empty=True,
        # A misspelled key in `.env` is an error, not silently ignored.
        extra="forbid",
    )

    anthropic_api_key: SecretStr | None = None
    model_answer: str = "claude-opus-5-5"
    model_small: str = "claude-haiku-5-5"
    effort_answer: Effort = "medium"
    effort_small: Effort = "low"
    mock_llm: bool = False
    adviser_contact: str = "ngan.visaa@gmail.com"
    database_path: str = "data/feedback.sqlite3"

    price_answer_input: Price = 4.00
    price_answer_output: Price = 20.00
    price_answer_cache_read: Price = 0.20
    price_answer_cache_write: Price = 5.00
    price_small_input: Price = 0.10
    price_small_output: Price = 0.50
    price_small_cache_read: Price = 0.01
    price_small_cache_write: Price = 0.125


@lru_cache
def get_settings() -> Settings:
    """Settings for the running app, loaded once."""
    return Settings()
