"""`content/demo-answers.yaml`: loading and the startup checks of demo mode (Story 4.2)."""

import re
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any

import pytest
import yaml

from app.adapters.file_content import load_content
from app.adapters.file_demo_answers import DemoContentError, load_demo_answers
from app.adapters.file_knowledge_base import load_knowledge_base
from app.main import CONTENT_FILE, DEMO_ANSWERS_FILE, KNOWLEDGE_BASE_DIR
from app.ports.content import ExampleQuestion
from tests.fakes.content import committed_checklists

THAI = re.compile("[\u0e00-\u0e7f]")
KB = load_knowledge_base(KNOWLEDGE_BASE_DIR)
EXAMPLES = tuple(
    load_content(CONTENT_FILE, "adviser@example.org", committed_checklists()).example_questions()
)
EXAMPLE = ExampleQuestion(id="visa-fee", th="ค่าธรรมเนียมเท่าไร", en="How much is the fee?")
SOURCE = "udi-fees"


def _answer(**changes: Any) -> dict[str, Any]:
    answer: dict[str, Any] = {"category": "general", "th": "90 ยูโร", "en": "90 euro", "sources": [SOURCE]}
    answer.update(changes)
    return answer


def _data(**changes: Any) -> dict[str, Any]:
    data: dict[str, Any] = {"answers": {EXAMPLE.id: _answer()}, "done_phrases": ["ขอบคุณ"]}
    data.update(changes)
    return data


def _write(tmp_path: Path, data: Any) -> Path:
    path = tmp_path / "demo-answers.yaml"
    path.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
    return path


def _load(tmp_path: Path, data: Any, examples: tuple[ExampleQuestion, ...] = (EXAMPLE,)):
    return load_demo_answers(_write(tmp_path, data), examples, KB)


def test_committed_file_loads_against_the_real_examples_and_knowledge_base() -> None:
    demo = load_demo_answers(DEMO_ANSWERS_FILE, EXAMPLES, KB)

    assert list(demo.answers) == [q.id for q in EXAMPLES]
    for answer in demo.answers.values():
        assert THAI.search(answer.th), answer.id
        assert not THAI.search(answer.en), answer.id
        assert answer.source_ids
        for source_id in answer.source_ids:
            KB.source(source_id)  # raises KeyError if unknown
    assert demo.done_phrases


def test_committed_done_phrases_have_thai_and_english_thanks() -> None:
    phrases = load_demo_answers(DEMO_ANSWERS_FILE, EXAMPLES, KB).done_phrases

    assert "ขอบคุณค่ะ" in phrases
    assert "thank you" in phrases
    assert any(not THAI.search(p) for p in phrases)


def test_how_to_start_gives_the_four_steps_in_order_with_websites() -> None:
    th = load_demo_answers(DEMO_ANSWERS_FILE, EXAMPLES, KB).answers["how-to-start"].th

    positions = [
        th.index(marker) for marker in ("1.", "norway.no", "2.", "udi.no", "3.", "4.", "vfsglobal.com")
    ]
    assert positions == sorted(positions)
    # Step 3 (pay) is on udi.no too.
    step3 = th[th.index("3.") : th.index("4.")]
    assert "udi.no" in step3


def test_valid_file_loads_and_is_immutable(tmp_path: Path) -> None:
    demo = _load(tmp_path, _data())

    answer = demo.answers[EXAMPLE.id]
    assert (answer.id, answer.category, answer.th, answer.en, answer.source_ids) == (
        EXAMPLE.id,
        "general",
        "90 ยูโร",
        "90 euro",
        (SOURCE,),
    )
    assert demo.done_phrases == ("ขอบคุณ",)
    with pytest.raises(TypeError):
        demo.answers["other"] = answer  # type: ignore[index]
    with pytest.raises(FrozenInstanceError):
        answer.th = "x"  # type: ignore[misc]


def test_missing_demo_answer_names_the_id(tmp_path: Path) -> None:
    other = ExampleQuestion(id="processing-time", th="ใช้เวลานานเท่าไร", en="How long?")

    with pytest.raises(DemoContentError, match="processing-time"):
        _load(tmp_path, _data(), (EXAMPLE, other))


def test_answer_for_an_unknown_example_is_rejected(tmp_path: Path) -> None:
    data = _data(answers={EXAMPLE.id: _answer(), "no-such-example": _answer()})

    with pytest.raises(DemoContentError, match="no-such-example"):
        _load(tmp_path, data)


def test_unknown_source_names_both_ids(tmp_path: Path) -> None:
    data = _data(answers={EXAMPLE.id: _answer(sources=[SOURCE, "no-such-source"])})

    with pytest.raises(DemoContentError) as caught:
        _load(tmp_path, data)

    assert EXAMPLE.id in str(caught.value)
    assert "no-such-source" in str(caught.value)


@pytest.mark.parametrize("category", ["generic", "", None, 3, ["general"], {"a": 1}, "done"])
def test_invalid_category_is_rejected(tmp_path: Path, category: object) -> None:
    with pytest.raises(DemoContentError, match="invalid category"):
        _load(tmp_path, _data(answers={EXAMPLE.id: _answer(category=category)}))


@pytest.mark.parametrize("done_phrases", [[], None, "ขอบคุณ", [""], ["  "], [3]])
def test_done_phrases_missing_or_empty_is_rejected(tmp_path: Path, done_phrases: object) -> None:
    with pytest.raises(DemoContentError, match=r"done.phrase"):
        _load(tmp_path, _data(done_phrases=done_phrases))


def test_done_phrases_key_missing_is_rejected(tmp_path: Path) -> None:
    data = _data()
    del data["done_phrases"]

    with pytest.raises(DemoContentError, match="done_phrases"):
        _load(tmp_path, data)


def test_thai_answer_without_thai_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DemoContentError, match="no Thai"):
        _load(tmp_path, _data(answers={EXAMPLE.id: _answer(th="90 euro")}))


@pytest.mark.parametrize(
    "changes",
    [
        {"th": ""},
        {"en": "  "},
        {"en": None},
        {"sources": []},
        {"sources": "udi-fees"},
        {"sources": [SOURCE, SOURCE]},
    ],
    ids=["empty-th", "blank-en", "null-en", "no-sources", "sources-string", "duplicate-source"],
)
def test_bad_answer_fields_are_rejected(tmp_path: Path, changes: dict[str, Any]) -> None:
    with pytest.raises(DemoContentError, match=EXAMPLE.id):
        _load(tmp_path, _data(answers={EXAMPLE.id: _answer(**changes)}))


def test_unknown_answer_field_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(DemoContentError, match="unknown field"):
        _load(tmp_path, _data(answers={EXAMPLE.id: _answer(note="x")}))


@pytest.mark.parametrize("data", [None, [], "text", {"answers": {}, "done_phrases": ["ok"], "extra": 1}])
def test_malformed_structure_is_rejected(tmp_path: Path, data: object) -> None:
    with pytest.raises(DemoContentError):
        _load(tmp_path, data)


def test_duplicate_yaml_key_is_rejected(tmp_path: Path) -> None:
    path = tmp_path / "demo-answers.yaml"
    path.write_text("answers: {}\nanswers: {}\ndone_phrases: [ok]\n", encoding="utf-8")

    with pytest.raises(DemoContentError, match="duplicate key"):
        load_demo_answers(path, (EXAMPLE,), KB)


def test_missing_file_and_bad_yaml(tmp_path: Path) -> None:
    with pytest.raises(DemoContentError, match="cannot read"):
        load_demo_answers(tmp_path / "missing.yaml", (EXAMPLE,), KB)

    bad = tmp_path / "bad.yaml"
    bad.write_text("answers: [unclosed\n", encoding="utf-8")
    with pytest.raises(DemoContentError, match="invalid YAML"):
        load_demo_answers(bad, (EXAMPLE,), KB)
