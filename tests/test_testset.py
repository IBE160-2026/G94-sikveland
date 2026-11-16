"""`eval/testset.yaml`: the evaluation test set and its loader (Story 5.1, NFR4).

No model or network call: the committed file is checked against the real knowledge
base and the real personal-information filter only.
"""

import re
from collections import Counter
from dataclasses import FrozenInstanceError
from pathlib import Path
from typing import Any, get_args

import pytest
import yaml

import scripts.testset as testset
from app.adapters.file_knowledge_base import load_knowledge_base
from app.main import CONTENT_FILE, KNOWLEDGE_BASE_DIR
from app.pipeline.filter import REMOVED_MARKER, remove_personal_info
from app.ports.llm import Category, Exchange
from app.web.request_log import Outcome
from scripts.testset import TESTSET_FILE, TestCase, TestsetError, load_testset

KB = load_knowledge_base(KNOWLEDGE_BASE_DIR)
CASES = load_testset(TESTSET_FILE, KB)

COVERAGE_TAGS = (
    "steps",
    "checklist",
    "sponsorship-form",
    "invitation-letter",
    "relationship-proof",
    "fee",
    "typo",
    "mixed-language",
    "follow-up",
)
_THAI_ID = re.compile(r"(?<![\d-])\d(?:[ -]?\d){12}(?![\d-])")
_PASSPORT = re.compile(r"(?<![A-Za-z])[A-Z]{2}\d{7}(?!\d)")
_PHONE = re.compile(r"(?<!\d)0\d{2}-\d{3}-\d{4}(?!\d)")
_NUMBER = re.compile(r"\d+(?:,\d{3})*")


def _of(**rule: str) -> list[TestCase]:
    ((name, value),) = rule.items()
    return [case for case in CASES if getattr(case, name) == value]


def _thai_id_check_digit(digits: str) -> int:
    total = sum(int(d) * (13 - i) for i, d in enumerate(digits[:12]))
    return (11 - total % 11) % 10


# --- The committed file ---------------------------------------------------------------------------


def test_committed_file_has_20_to_30_cases() -> None:
    assert 20 <= len(CASES) <= 30


def test_committed_file_covers_every_topic_by_tag() -> None:
    tags = Counter(tag for case in CASES for tag in case.tags)
    missing = [tag for tag in COVERAGE_TAGS if tags[tag] < 1]
    assert not missing, f"no case tagged {missing}"


def test_committed_file_has_enough_assessment_out_of_scope_and_no_answer_cases() -> None:
    assert len(_of(category="individual_assessment")) >= 2
    assert len(_of(category="out_of_scope")) >= 2
    assert len(_of(outcome="no_answer")) >= 4


def test_committed_file_asks_for_a_person_in_at_least_three_different_ways() -> None:
    reach = _of(category="reach_person")
    assert len({case.question for case in reach}) >= 3
    tags = {tag for case in reach for tag in case.tags}
    # Both kinds the classifier knows: asking for a person, and for help with the whole process.
    assert {"ask-person", "whole-process"} <= tags


def test_committed_file_covers_every_kind_of_personal_information() -> None:
    kinds = {kind for case in CASES for kind in case.personal_info}
    assert kinds == set(get_args(testset.PersonalInfo)) == {"thai_id", "passport", "phone"}


def test_committed_file_records_that_the_thai_awaits_review() -> None:
    header = TESTSET_FILE.read_text(encoding="utf-8").split("\ncases:")[0]

    # Unreviewed Thai stays a DRAFT until the user approves it as adviser review (NFR8).
    assert "NFR8" in header and ("DRAFT" in header or "approved" in header)


def test_committed_questions_do_not_copy_the_example_questions() -> None:
    texts = yaml.safe_load(CONTENT_FILE.read_text(encoding="utf-8"))
    examples = {question["th"] for question in texts["example-questions"]}
    assert len(examples) == 4
    copied = [case.id for case in CASES if case.question in examples]
    assert not copied


def test_every_number_in_an_expected_fact_is_in_a_cited_snapshot() -> None:
    # A cheap check that the facts come from the sources; the adviser checks the wording.
    for case in _of(outcome="answered"):
        texts = [KB.source(source_id).text for source_id in case.sources]
        for fact in case.facts:
            for number in _NUMBER.findall(fact):
                assert any(re.search(rf"(?<![\d,]){number}(?!\d|,\d)", t) for t in texts), (
                    case.id,
                    fact,
                    number,
                )


def test_expected_outcomes_are_request_log_outcomes() -> None:
    assert set(testset.OUTCOMES) <= set(get_args(Outcome))
    assert set(testset.CATEGORIES) == set(get_args(Category))


def test_cases_are_frozen_with_history_as_exchanges() -> None:
    follow_ups = [case for case in CASES if "follow-up" in case.tags]
    assert follow_ups
    for case in follow_ups:
        assert case.history and all(isinstance(turn, Exchange) for turn in case.history)
    with pytest.raises(FrozenInstanceError):
        CASES[0].question = "x"  # type: ignore[misc]


# --- The filter expectations ----------------------------------------------------------------------


@pytest.mark.parametrize(
    "case", [c for c in CASES if {"thai_id", "passport"} & set(c.personal_info)], ids=lambda c: c.id
)
def test_thai_id_and_passport_numbers_are_removed(case: TestCase) -> None:
    numbers = []
    if "thai_id" in case.personal_info:
        numbers += _THAI_ID.findall(case.question)
    if "passport" in case.personal_info:
        numbers += _PASSPORT.findall(case.question)
    assert numbers, case.id

    filtered = remove_personal_info(case.question)

    assert filtered.removed and REMOVED_MARKER in filtered.text
    digits_left = re.sub(r"\D", "", filtered.text)
    for number in numbers:
        assert number not in filtered.text
        assert re.sub(r"\D", "", number) not in digits_left


@pytest.mark.parametrize("case", [c for c in CASES if "thai_id" in c.personal_info], ids=lambda c: c.id)
def test_thai_id_numbers_are_made_up_with_a_wrong_check_digit(case: TestCase) -> None:
    numbers = _THAI_ID.findall(case.question)
    assert numbers, case.id
    for number in numbers:
        digits = re.sub(r"\D", "", number)
        assert int(digits[-1]) != _thai_id_check_digit(digits), (case.id, number)


@pytest.mark.parametrize("case", [c for c in CASES if "phone" in c.personal_info], ids=lambda c: c.id)
def test_phone_numbers_are_kept(case: TestCase) -> None:
    assert _PHONE.search(case.question), case.id
    if set(case.personal_info) == {"phone"}:
        assert remove_personal_info(case.question).text == case.question


@pytest.mark.parametrize("case", [c for c in CASES if not c.personal_info], ids=lambda c: c.id)
def test_cases_without_personal_information_pass_the_filter_unchanged(case: TestCase) -> None:
    assert remove_personal_info(case.question).text == case.question
    assert not _THAI_ID.search(case.question) and not _PASSPORT.search(case.question)


def test_history_never_holds_personal_information() -> None:
    for case in CASES:
        for turn in case.history:
            for text in (turn.question, turn.answer):
                assert remove_personal_info(text).text == text, case.id


# --- The loader's rules, on written files -------------------------------------------------------

_DROP = object()  # leaves the field out of the written case


def _case(**changes: Any) -> dict[str, Any]:
    case: dict[str, Any] = {
        "id": "fee-question",
        "question": "ค่าวีซ่าเท่าไร",
        "en": "How much is the visa?",
        "category": "general",
        "outcome": "answered",
        "facts": ["The visa fee is EUR 90 for an adult"],
        "sources": ["udi-fees"],
        "tags": ["fee"],
    }
    case.update(changes)
    return {key: value for key, value in case.items() if value is not _DROP}


def _load(tmp_path: Path, *cases: dict[str, Any], data: Any = None) -> list[TestCase]:
    path = tmp_path / "testset.yaml"
    content = data if data is not None else {"cases": list(cases)}
    path.write_text(yaml.safe_dump(content, allow_unicode=True), encoding="utf-8")
    return load_testset(path, KB)


def _fails(tmp_path: Path, *cases: dict[str, Any], match: str) -> None:
    with pytest.raises(TestsetError, match=match):
        _load(tmp_path, *cases)


def test_a_valid_written_file_loads(tmp_path: Path) -> None:
    history = [{"question": "ต้องใช้เอกสารอะไร", "answer": "หนังสือเดินทางค่ะ"}]
    plain, follow_up = _load(
        tmp_path,
        _case(),
        _case(id="follow-up-fee", tags=["follow-up"], history=history, personal_info=["phone"]),
    )

    assert plain == TestCase(
        id="fee-question",
        question="ค่าวีซ่าเท่าไร",
        en="How much is the visa?",
        category="general",
        outcome="answered",
        facts=("The visa fee is EUR 90 for an adult",),
        sources=("udi-fees",),
        tags=("fee",),
    )
    assert follow_up.history == (Exchange("ต้องใช้เอกสารอะไร", "หนังสือเดินทางค่ะ"),)
    assert follow_up.personal_info == ("phone",)


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"sources": ["no-such-source"]}, "'fee-question' has unknown source id 'no-such-source'"),
        ({"category": "chitchat"}, "'fee-question' 'category' is 'chitchat'"),
        ({"outcome": "error"}, "'fee-question' 'outcome' is 'error'"),
        ({"outcome": "translated"}, "'fee-question' 'outcome' is 'translated'"),
        ({"personal_info": ["email"]}, "'fee-question' 'personal_info' is 'email'"),
        ({"personal_info": ["phone", "phone"]}, "'fee-question' lists a 'personal_info' kind more than once"),
        ({"sources": ["udi-fees", "udi-fees"]}, "'fee-question' lists source 'udi-fees' more than once"),
        ({"tags": ["Fee"]}, "'fee-question' has a tag that is not kebab-case"),
        ({"tags": ["fee", "fee"]}, "'fee-question' lists tag 'fee' more than once"),
        ({"question": "How much?"}, "'fee-question' 'question' contains no Thai"),
        ({"en": "ค่าวีซ่า"}, "'fee-question' 'en' must be English"),
        ({"facts": ["ค่าวีซ่า 90 ยูโร"]}, "'fee-question' fact must be English"),
        ({"facts": "EUR 90"}, "'fee-question' 'facts' must be a list"),
        ({"question": "  "}, "'fee-question' 'question' must be a non-empty string"),
    ],
)
def test_a_bad_value_is_reported_with_the_case_id(
    tmp_path: Path, changes: dict[str, Any], match: str
) -> None:
    _fails(tmp_path, _case(**changes), match=re.escape(match))


def test_a_missing_field_is_reported_with_the_case_id(tmp_path: Path) -> None:
    _fails(tmp_path, _case(tags=_DROP), match=re.escape("case 'fee-question' is missing field(s): tags"))


def test_an_extra_field_is_reported_with_the_case_id(tmp_path: Path) -> None:
    _fails(tmp_path, _case(answer="90"), match=re.escape("case 'fee-question' has unknown field(s): answer"))


def test_a_duplicate_id_is_reported(tmp_path: Path) -> None:
    _fails(tmp_path, _case(), _case(), match="duplicate case id 'fee-question'")


@pytest.mark.parametrize("bad_id", ["Fee_Question", "fee question", "", 7, None])
def test_an_id_that_is_not_kebab_case_is_reported(tmp_path: Path, bad_id: object) -> None:
    _fails(
        tmp_path,
        _case(),
        _case(id=bad_id),
        match=re.escape(f"case #2 needs a kebab-case 'id', got {bad_id!r}"),
    )


def test_a_missing_id_is_reported_by_position(tmp_path: Path) -> None:
    _fails(tmp_path, _case(id=_DROP), match=re.escape("case #1 needs a kebab-case 'id', got None"))


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        (
            {"category": "out_of_scope", "outcome": "fixed_reply"},
            "a 'fixed_reply' case has no facts and no sources",
        ),
        ({"category": "out_of_scope", "outcome": "fixed_reply", "facts": []}, "has no facts and no sources"),
        ({"facts": []}, "an 'answered' case needs at least one fact and one source"),
        ({"sources": []}, "an 'answered' case needs at least one fact and one source"),
        ({"outcome": "no_answer"}, "a 'no_answer' case has no facts and no sources"),
        ({"outcome": "fixed_reply", "facts": [], "sources": []}, "a 'general' question expects 'answered'"),
        (
            {"category": "reach_person", "facts": [], "sources": []},
            "a 'reach_person' question expects 'fixed_reply'",
        ),
        ({"category": "done", "outcome": "no_answer", "facts": [], "sources": []}, "expects 'fixed_reply'"),
    ],
)
def test_an_inconsistent_case_is_reported(tmp_path: Path, changes: dict[str, Any], match: str) -> None:
    with pytest.raises(TestsetError, match=re.escape(match)) as error:
        _load(tmp_path, _case(**changes))
    assert str(error.value).startswith("case 'fee-question': ")


def test_consistent_fixed_reply_and_no_answer_cases_load(tmp_path: Path) -> None:
    cases = _load(
        tmp_path,
        _case(id="a", category="individual_assessment", outcome="fixed_reply", facts=[], sources=[]),
        _case(id="b", outcome="no_answer", facts=[], sources=[]),
    )
    assert [(c.category, c.outcome) for c in cases] == [
        ("individual_assessment", "fixed_reply"),
        ("general", "no_answer"),
    ]


@pytest.mark.parametrize(
    ("changes", "match"),
    [
        ({"tags": ["follow-up"]}, "must have 'history' exactly when it is tagged 'follow-up'"),
        (
            {"history": [{"question": "ต้องใช้อะไร", "answer": "หนังสือเดินทาง"}]},
            "must have 'history' exactly when it is tagged 'follow-up'",
        ),
        (
            {"tags": ["follow-up"], "history": [{"question": "ต้องใช้อะไร", "answer": "หนังสือเดินทาง"}] * 3},
            "'history' has 3 exchanges; at most 2",
        ),
        (
            {"tags": ["follow-up"], "history": [{"question": "ต้องใช้อะไร"}]},
            "history exchange #1 must be a mapping with exactly 'question' and 'answer'",
        ),
        (
            {"tags": ["follow-up"], "history": [{"question": "ต้องใช้อะไร", "answer": "a passport"}]},
            "history exchange #1 'answer' contains no Thai",
        ),
        (
            {"tags": ["follow-up"], "history": [{"question": "What do I need?", "answer": "หนังสือเดินทาง"}]},
            "history exchange #1 'question' contains no Thai",
        ),
    ],
)
def test_a_bad_history_is_reported_with_the_case_id(
    tmp_path: Path, changes: dict[str, Any], match: str
) -> None:
    _fails(tmp_path, _case(**changes), match=re.escape(f"case 'fee-question' {match}"))


@pytest.mark.parametrize(
    ("data", "match"),
    [
        ([_case()], "exactly one key, 'cases'"),
        ({"cases": [], "extra": 1}, "exactly one key, 'cases'"),
        ({"cases": []}, "must be a non-empty list"),
        ({"cases": ["not a mapping"]}, "case #1 must be a mapping"),
    ],
)
def test_a_malformed_file_is_reported(tmp_path: Path, data: Any, match: str) -> None:
    with pytest.raises(TestsetError, match=re.escape(match)):
        _load(tmp_path, data=data)


def test_a_duplicate_key_and_a_missing_file_are_reported(tmp_path: Path) -> None:
    path = tmp_path / "testset.yaml"
    path.write_text("cases: []\ncases: []\n", encoding="utf-8")
    with pytest.raises(TestsetError, match="duplicate key 'cases'"):
        load_testset(path, KB)
    with pytest.raises(TestsetError, match="cannot read test set"):
        load_testset(tmp_path / "missing.yaml", KB)
