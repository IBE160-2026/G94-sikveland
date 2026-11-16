"""The README stays complete for the examiner (Story 4.3, NFR2).

Every setting in `.env.example` has its own row in the settings table, and every example
question appears with its Thai, English and Norwegian text, so neither can be added
without the README following.
"""

import re

import pytest

from app.adapters.file_content import load_content
from app.main import CONTENT_FILE, ROOT
from tests.fakes.content import committed_checklists

README = (ROOT / "README.md").read_text(encoding="utf-8")
ENV_EXAMPLE = (ROOT / ".env.example").read_text(encoding="utf-8")
# Settings in `.env.example`, also commented-out ones (`# NAME=`).
SETTINGS = sorted(set(re.findall(r"^#?\s*([A-Z][A-Z0-9_]+)=", ENV_EXAMPLE, flags=re.MULTILINE)))
EXAMPLES = load_content(CONTENT_FILE, "adviser@example.org", committed_checklists()).example_questions()


def _settings_rows() -> list[str]:
    start = README.index("### Innstillinger")
    end = README.index("\n## ", start)
    return [line for line in README[start:end].splitlines() if line.startswith("| `")]


def test_env_example_has_settings() -> None:
    assert "ANTHROPIC_API_KEY" in SETTINGS
    assert len(SETTINGS) >= 20


@pytest.mark.parametrize("name", SETTINGS)
def test_every_setting_has_a_row_in_the_settings_table(name: str) -> None:
    rows = [row for row in _settings_rows() if f"`{name}`" in row.split("|")[1]]

    assert rows, f"{name} from .env.example has no row in the README settings table"
    # Default and meaning are filled in.
    cells = [cell.strip() for cell in rows[0].strip("|").split("|")]
    assert len(cells) == 3 and all(cells), rows[0]


def _example_rows() -> list[list[str]]:
    start = README.index("| Eksempelspørsmål (thai) | In English | På norsk |")
    lines = README[start:].splitlines()[2:]
    rows = []
    for line in lines:
        if not line.startswith("|"):
            break
        rows.append([cell.strip() for cell in line.strip("|").split("|")])
    return rows


def test_every_example_question_is_listed_in_thai_english_and_norwegian() -> None:
    rows = _example_rows()

    assert [row[0] for row in rows] == [question.th for question in EXAMPLES]
    for row, question in zip(rows, EXAMPLES, strict=True):
        assert row[1] == question.en
        assert row[2], f"no Norwegian for {question.id}"


# The default of every price in `.env.example`, which the README must repeat.
PRICES = dict(re.findall(r"^(PRICE_[A-Z_]+)=(\S+)", ENV_EXAMPLE, flags=re.MULTILINE))


def test_there_are_eight_prices() -> None:
    assert len(PRICES) == 8


@pytest.mark.parametrize("name", sorted(PRICES))
def test_every_price_row_shows_the_default_from_env_example(name: str) -> None:
    [row] = [row for row in _settings_rows() if row.split("|")[1].strip() == f"`{name}`"]

    assert row.split("|")[2].strip() == f"`{PRICES[name]}`"


def test_the_readme_explains_both_shells_the_phone_and_the_cost_log() -> None:
    # Demo mode and `.env` in both shells.
    assert '$env:MOCK_LLM = "true"' in README and "MOCK_LLM=true uv run uvicorn app.main:app" in README
    assert "Copy-Item .env.example .env" in README and "cp .env.example .env" in README
    # The phone on the same Wi-Fi, in demo mode too.
    assert "MOCK_LLM=true uv run uvicorn app.main:app --host 0.0.0.0" in README
    assert "ipconfig" in README and "hostname -I" in README
    assert "uv run pytest" in README
    assert "## Forespørselslogg" in README and "Kostnad per spørsmål" in README
