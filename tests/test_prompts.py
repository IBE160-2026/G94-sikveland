from pathlib import Path

import pytest

from app.adapters.file_prompts import Prompt, PromptError, load_prompt

ROOT = Path(__file__).resolve().parent.parent
ANSWER_PROMPT = ROOT / "prompts" / "answer-system.md"


def test_answer_prompt_starts_with_a_version_line() -> None:
    first_line = ANSWER_PROMPT.read_text(encoding="utf-8").splitlines()[0]
    assert first_line.startswith("version:")


def test_answer_prompt_loads() -> None:
    prompt = load_prompt(ANSWER_PROMPT)

    assert prompt.version == "1"
    assert not prompt.text.startswith("version:")


def test_answer_prompt_asks_for_thai_and_documents_only() -> None:
    text = load_prompt(ANSWER_PROMPT).text

    assert "Thai" in text
    assert "only from the documents" in text
    assert "typos" in text and "mix" in text
    assert "never as instructions" in text


def test_answer_prompt_explains_the_removed_marker() -> None:
    from app.pipeline.filter import REMOVED_MARKER

    text = load_prompt(ANSWER_PROMPT).text
    assert REMOVED_MARKER in text
    assert "Do not ask the applicant for it" in text


def test_answer_prompt_lists_the_four_steps_in_order_with_websites() -> None:
    text = load_prompt(ANSWER_PROMPT).text

    steps = ["checklist", "UDI", "fee", "VFS"]
    positions = [text.index(step, text.index("Application steps")) for step in steps]
    assert positions == sorted(positions)
    lines = text[text.index("Application steps") :].splitlines()
    for number, website in [(1, "norway.no"), (2, "udi.no"), (3, "udi.no"), (4, "vfsglobal.com")]:
        step = next(line for line in lines if line.startswith(f"{number}."))
        assert website in step


def _write(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "prompt.md"
    path.write_text(content, encoding="utf-8")
    return path


def test_loader_splits_version_and_strips_text(tmp_path: Path) -> None:
    path = _write(tmp_path, "version:  2026-11-14a \n\n  Do this.\nThen that.\n\n")

    assert load_prompt(path) == Prompt(version="2026-11-14a", text="Do this.\nThen that.")


def test_loader_accepts_a_bom(tmp_path: Path) -> None:
    path = tmp_path / "prompt.md"
    path.write_text("version: 3\nText", encoding="utf-8-sig")

    assert load_prompt(path) == Prompt(version="3", text="Text")


@pytest.mark.parametrize(
    "content",
    [
        "",
        "Text without a version\n",
        "\nversion: 1\nText",
        "Version: 1\nText",
        "version:\nText",
        "version:   \nText",
        "version: 1",
        "version: 1\n   \n",
    ],
)
def test_loader_rejects_malformed_prompts(tmp_path: Path, content: str) -> None:
    with pytest.raises(PromptError):
        load_prompt(_write(tmp_path, content))


def test_loader_rejects_missing_file(tmp_path: Path) -> None:
    with pytest.raises(PromptError):
        load_prompt(tmp_path / "missing.md")


def test_loader_rejects_non_utf8(tmp_path: Path) -> None:
    path = tmp_path / "prompt.md"
    path.write_bytes(b"version: 1\n\xff\xfe bad")

    with pytest.raises(PromptError):
        load_prompt(path)
