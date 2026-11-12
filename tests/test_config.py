from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import Settings

ROOT = Path(__file__).resolve().parent.parent


def test_defaults_without_env_file(settings: Settings) -> None:
    assert settings.anthropic_api_key is None
    assert settings.model_answer == "claude-opus-5-5"
    assert settings.model_small == "claude-haiku-5-5"
    assert settings.effort_answer == "medium"
    assert settings.effort_small == "low"
    assert settings.mock_llm is False
    assert settings.database_path == "data/feedback.sqlite3"


def test_env_var_overrides_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("EFFORT_ANSWER", "high")
    monkeypatch.setenv("MOCK_LLM", "true")

    settings = Settings(_env_file=None)

    assert settings.effort_answer == "high"
    assert settings.mock_llm is True


def test_reads_env_file(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "ANTHROPIC_API_KEY=test-key\nADVISER_CONTACT=adviser@example.com\nPRICE_ANSWER_INPUT=1.5\n",
        encoding="utf-8",
    )

    settings = Settings(_env_file=env_file)

    assert settings.anthropic_api_key is not None
    assert settings.anthropic_api_key.get_secret_value() == "test-key"
    assert settings.adviser_contact == "adviser@example.com"
    assert settings.price_answer_input == 1.5


@pytest.mark.parametrize("env_name", ["EFFORT_ANSWER", "EFFORT_SMALL"])
def test_invalid_effort_fails(monkeypatch: pytest.MonkeyPatch, env_name: str) -> None:
    monkeypatch.setenv(env_name, "extreme")

    with pytest.raises(ValidationError, match=env_name.lower()):
        Settings(_env_file=None)


@pytest.mark.parametrize("value", ["-1", "nan", "inf"])
def test_invalid_price_fails(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("PRICE_ANSWER_INPUT", value)

    with pytest.raises(ValidationError, match="price_answer_input"):
        Settings(_env_file=None)


def test_reads_env_file_with_bom(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_bytes(b"\xef\xbb\xbfEFFORT_ANSWER=high\n")

    assert Settings(_env_file=env_file).effort_answer == "high"


def test_misspelled_key_in_env_file_fails(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text("MOCK_LMM=true\n", encoding="utf-8")

    with pytest.raises(ValidationError, match="mock_lmm"):
        Settings(_env_file=env_file)


def test_env_example_lists_every_setting() -> None:
    lines = (ROOT / ".env.example").read_text(encoding="utf-8").splitlines()
    keys = {
        line.split("=", 1)[0].strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    }

    assert keys == {name.upper() for name in Settings.model_fields}


def test_env_example_values_are_valid() -> None:
    settings = Settings(_env_file=ROOT / ".env.example")

    assert settings.anthropic_api_key is None
    assert settings == Settings(_env_file=None)


@pytest.mark.parametrize("value", ["  ", "\t"])
def test_blank_adviser_contact_fails(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv("ADVISER_CONTACT", value)

    with pytest.raises(ValidationError, match="adviser_contact"):
        Settings(_env_file=None)


def test_adviser_contact_is_stripped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ADVISER_CONTACT", "  adviser@example.com ")

    assert Settings(_env_file=None).adviser_contact == "adviser@example.com"
