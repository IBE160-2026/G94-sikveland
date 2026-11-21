"""`scripts/run_eval.py`: the evaluation run and `--score` (Story 5.2, NFR4, SM-2).

No network: every run injects a `ScriptedLLM` (one per case, in order) into `create_app`,
reads a small test set written to `tmp_path` and writes its report there.
"""

import io
import json
import re
from collections.abc import Callable, Iterator, Sequence
from datetime import date
from pathlib import Path
from typing import get_args

import pytest
import yaml
from fastapi.testclient import TestClient

import scripts.run_eval as run_eval
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.file_prompts import load_prompt
from app.adapters.ollama_llm import CLOSEST_ID_CUTOFF, resolve_source_id
from app.config import Settings
from app.main import (
    ANSWER_PROMPT_FILE,
    CITING_PROMPT_FILE,
    CLASSIFIER_PROMPT_FILE,
    KNOWLEDGE_BASE_DIR,
    create_app,
)
from app.pipeline.cost import cost_usd
from app.ports.llm import AnswerChunk, Category, Exchange, LLMError, Usage
from app.web.chat import FIXED_REPLY_KEYS
from app.web.request_log import answer_prices, small_prices
from scripts.testset import TestCase
from tests.fakes.fake_llm import CLASSIFY_USAGE, DEFAULT_USAGE, ScriptedLLM

KB = load_knowledge_base(KNOWLEDGE_BASE_DIR)
TODAY = date(2026, 11, 16)
ANSWER_VERSION = load_prompt(ANSWER_PROMPT_FILE).version
CLASSIFIER_VERSION = load_prompt(CLASSIFIER_PROMPT_FILE).version
CITING_VERSION = load_prompt(CITING_PROMPT_FILE).version
STEM = f"2026-11-16-answer-{ANSWER_VERSION}-classifier-{CLASSIFIER_VERSION}"
THAI_ANSWER = "ค่าธรรมเนียมวีซ่าจ่ายออนไลน์"

FEE_CASE = {
    "id": "visa-fee",
    "question": "ค่าวีซ่าเท่าไหร่คะ หนังสือเดินทาง AB1234567",
    "en": "How much is the visa fee? Passport AB1234567",
    "category": "general",
    "outcome": "answered",
    "facts": ["The fee is paid online"],
    "sources": ["udi-fees"],
    "tags": ["fee"],
    "personal_info": ["passport"],
}
FOLLOW_UP_CASE = {
    "id": "fee-follow-up",
    "question": "แล้วจ่ายตอนไหนคะ",
    "en": "And when do I pay?",
    "category": "general",
    "outcome": "answered",
    "facts": ["The fee is paid when the application is registered"],
    "sources": ["udi-fees", "udi-how-to-apply-visitor-visa"],
    "tags": ["fee", "follow-up"],
    "history": [{"question": "ค่าวีซ่าเท่าไหร่คะ", "answer": "ค่าวีซ่าคือ 90 ยูโร"}],
}
NO_ANSWER_CASE = {
    "id": "not-covered",
    "question": "สนามบินมีที่จอดรถไหมคะ",
    "en": "Is there parking at the airport?",
    "category": "general",
    "outcome": "no_answer",
    "facts": [],
    "sources": [],
    "tags": ["no-answer"],
}
CHANCES_CASE = {
    "id": "my-chances",
    "question": "ฉันจะได้วีซ่าไหมคะ",
    "en": "Will I get the visa?",
    "category": "individual_assessment",
    "outcome": "fixed_reply",
    "facts": [],
    "sources": [],
    "tags": ["individual-assessment"],
}
PERSON_CASE = {
    "id": "talk-to-person",
    "question": "ขอคุยกับคนได้ไหมคะ โทร 081-234-5678",
    "en": "Can I talk to a person? Phone 081-234-5678",
    "category": "reach_person",
    "outcome": "fixed_reply",
    "facts": [],
    "sources": [],
    "tags": ["reach-person"],
    "personal_info": ["phone"],
}
OUT_OF_SCOPE_CASE = {
    "id": "work-permit",
    "question": "ขอวีซ่าทำงานยังไงคะ",
    "en": "How do I apply for a work visa?",
    "category": "out_of_scope",
    "outcome": "fixed_reply",
    "facts": [],
    "sources": [],
    "tags": ["out-of-scope"],
}
THAI_ID_CASE = {
    "id": "id-number-chances",
    "question": "เลขบัตรประชาชน 3-1012-34567-89-5 ฉันจะได้วีซ่าไหมคะ",
    "en": "(Gives a made-up Thai ID number.) Will I get the visa?",
    "category": "individual_assessment",
    "outcome": "fixed_reply",
    "facts": [],
    "sources": [],
    "tags": ["individual-assessment"],
    "personal_info": ["thai_id"],
}
ALL_CASES = [FEE_CASE, FOLLOW_UP_CASE, NO_ANSWER_CASE, CHANCES_CASE, PERSON_CASE, OUT_OF_SCOPE_CASE]


class CaseByCaseLLM:
    """One `ScriptedLLM` per case, in run order: each classify call moves to the next one."""

    def __init__(self, scripts: Sequence[ScriptedLLM]) -> None:
        self.scripts = list(scripts)
        self.index = -1

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        self.index += 1
        return self.scripts[self.index].classify(question, recent_history)

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        return self.scripts[self.index].answer(question, history)

    def translate(self, text: str) -> tuple[str, Usage]:
        raise AssertionError("the evaluation never translates")


def _answered(*source_ids: str) -> ScriptedLLM:
    return ScriptedLLM(chunks=[AnswerChunk(THAI_ANSWER, source_ids)], category="general")


def _uncited() -> ScriptedLLM:
    return ScriptedLLM(chunks=[AnswerChunk("ข้อความที่ไม่มีแหล่งที่มา")], category="general")


def _fixed(category: str) -> ScriptedLLM:
    return ScriptedLLM(category=category)


def _all_match() -> list[ScriptedLLM]:
    return [
        _answered("udi-fees"),
        _answered("udi-how-to-apply-visitor-visa"),
        _uncited(),
        _fixed("individual_assessment"),
        _fixed("reach_person"),
        _fixed("out_of_scope"),
    ]


@pytest.fixture
def claude(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        anthropic_api_key="sk-test-not-used",
        request_log_path=str(tmp_path / "requests.jsonl"),
        database_path=str(tmp_path / "feedback.sqlite3"),
    )


def _testset(tmp_path: Path, cases: Sequence[dict]) -> Path:
    path = tmp_path / "testset.yaml"
    path.write_text(yaml.safe_dump({"cases": list(cases)}, allow_unicode=True), encoding="utf-8")
    return path


def _run(
    settings: Settings,
    tmp_path: Path,
    cases: Sequence[dict],
    llm: object,
) -> tuple[int, str, str, Path]:
    out, err = io.StringIO(), io.StringIO()
    code = run_eval.run(
        settings,
        out,
        err,
        llm=llm,  # type: ignore[arg-type]
        today=TODAY,
        testset_file=_testset(tmp_path, cases),
        reports_dir=tmp_path / "reports",
    )
    return code, out.getvalue(), err.getvalue(), tmp_path / "reports"


def _report(reports: Path) -> str:
    (path,) = sorted(reports.glob("*.md"))
    return path.read_text(encoding="utf-8")


def _case_data(report: str) -> dict[str, dict]:
    found = re.findall(r"^<!-- eval-case (\{.*\}) -->$", report, flags=re.MULTILINE)
    return {data["id"]: data for data in map(json.loads, found)}


def _section(report: str, case_id: str) -> str:
    start = report.index(f"`{case_id}`\n")
    end = report.find("\n### ", start)
    return report[start : end if end != -1 else None]


def _fill(report: str, judgements: dict[str, str]) -> str:
    for case_id, value in judgements.items():
        section = _section(report, case_id)
        report = report.replace(section, section.replace("\nAdviser: ", f"\nAdviser: {value}", 1))
    return report


# --- Refused runs ---------------------------------------------------------------------------------


def test_demo_mode_is_refused_before_any_call(tmp_path: Path, claude: Settings) -> None:
    llm = ScriptedLLM()
    demo = claude.model_copy(update={"mock_llm": True})
    code, _, err, reports = _run(demo, tmp_path, ALL_CASES, llm)
    assert code == 2
    assert "MOCK_LLM" in err
    assert llm.classify_calls == [] and llm.calls == []
    assert not reports.exists()


def test_claude_without_a_key_is_refused_before_any_call(tmp_path: Path, settings: Settings) -> None:
    llm = ScriptedLLM()
    code, _, err, reports = _run(settings, tmp_path, ALL_CASES, llm)
    assert code == 2
    assert "ANTHROPIC_API_KEY" in err
    assert llm.classify_calls == [] and llm.calls == []
    assert not reports.exists()


def test_a_blank_key_counts_as_missing(tmp_path: Path, settings: Settings) -> None:
    blank = Settings(_env_file=None, anthropic_api_key="  ", request_log_path=settings.request_log_path)
    assert run_eval.refusal(blank) is not None


def test_main_refuses_demo_mode_from_the_settings(monkeypatch: pytest.MonkeyPatch, claude: Settings) -> None:
    monkeypatch.setattr(run_eval, "get_settings", lambda: claude.model_copy(update={"mock_llm": True}))
    assert run_eval.main([]) == 2


# --- A run --------------------------------------------------------------------------------------


def test_all_match_passes_every_check_and_sums_tokens_and_cost(tmp_path: Path, claude: Settings) -> None:
    scripts = _all_match()
    code, out, err, reports = _run(claude, tmp_path, ALL_CASES, CaseByCaseLLM(scripts))
    assert code == 0, err
    report = _report(reports)

    assert (reports / f"{STEM}.md").exists()
    data = _case_data(report)
    assert list(data) == [case["id"] for case in ALL_CASES]
    for case_id, case in data.items():
        assert all(case["checks"][name] for name in run_eval.CHECKS), case_id
    assert data["visa-fee"]["target"] == "general"
    assert data["not-covered"]["target"] == "no_answer"
    assert data["my-chances"]["target"] == "individual_assessment"
    assert data["talk-to-person"]["target"] == "reach_person"
    assert data["work-permit"]["target"] is None

    # 6 classify calls and 3 answer calls (the no-answer case calls the answer model too).
    tokens = (
        6 * CLASSIFY_USAGE.input_tokens + 3 * DEFAULT_USAGE.input_tokens,
        6 * CLASSIFY_USAGE.output_tokens + 3 * DEFAULT_USAGE.output_tokens,
    )
    cost = round(
        6 * cost_usd(CLASSIFY_USAGE, small_prices(claude))
        + 3 * cost_usd(DEFAULT_USAGE, answer_prices(claude)),
        6,
    )
    assert f"- Tokens: input {tokens[0]}, output {tokens[1]}, cache read 0, cache write 0" in report
    assert f"- Total cost: {cost:.6f} USD" in report
    assert "- Provider: anthropic" in report
    assert f"- Answer model: `{claude.model_answer}`" in report
    assert f"- Classify model: `{claude.model_small}`" in report
    assert f"- Prompt versions: answer {ANSWER_VERSION}, classifier {CLASSIFIER_VERSION}" in report
    assert "- Cases: 6" in report

    sources = KB.documents()
    newest = max(source.retrieved for source in sources).isoformat()
    assert f"- Knowledge base: {len(sources)} sources, newest retrieved {newest}" in report

    # Totals: general awaits the adviser, the other three targets are met; each row by its label.
    assert (
        "| General questions correct, with the correct source | ≥ 90% | awaiting adviser: 2 of 2 pass "
        "the automatic checks, 0 judged correct, 2 not judged yet | awaiting adviser |"
    ) in report
    assert '| Individual assessment gets "the embassy decides" | 100% | 1 of 1 (100%) | yes |' in report
    assert "| Not covered by the sources gets the no-answer message | 100% | 1 of 1 (100%) | yes |" in report
    assert "| Request for a person gets the adviser contact | 100% | 1 of 1 (100%) | yes |" in report
    assert "- Cases that dropped unknown source ids: 0 of 6" in report

    # A follow-up shows its earlier question and answer.
    follow_up = _section(report, "fee-follow-up")
    assert "- Earlier question 1: ค่าวีซ่าเท่าไหร่คะ" in follow_up
    assert "- Earlier answer 1: ค่าวีซ่าคือ 90 ยูโร" in follow_up

    # One section per case with the texts and an empty adviser line.
    fee = _section(report, "visa-fee")
    assert FEE_CASE["question"] in fee
    assert FEE_CASE["en"] in fee
    assert "- Category: expected `general`, actual `general`" in fee
    assert "- Outcome: expected `answered`, actual `answered`" in fee
    assert "- Cited sources: `udi-fees`" in fee
    assert f"> {THAI_ANSWER}" in fee
    assert "- The fee is paid online" in fee
    assert fee.rstrip().endswith("Adviser:")
    assert report.count("\nAdviser: \n") == len(ALL_CASES)

    # The case's history and the cleaned question went to the model.
    assert scripts[1].calls[0].history == (Exchange("ค่าวีซ่าเท่าไหร่คะ", "ค่าวีซ่าคือ 90 ยูโร"),)
    assert "AB1234567" not in scripts[0].classify_calls[0].question

    # The console names case ids only, never question or reply text.
    assert "visa-fee" in out and FEE_CASE["question"] not in out and THAI_ANSWER not in out


def test_no_request_log_line_is_written(tmp_path: Path, claude: Settings) -> None:
    code, *_ = _run(claude, tmp_path, ALL_CASES, CaseByCaseLLM(_all_match()))
    assert code == 0
    assert not Path(claude.request_log_path).exists()


def test_no_citation_is_no_answer(tmp_path: Path, claude: Settings) -> None:
    cases = [FEE_CASE, NO_ANSWER_CASE]
    code, *_, reports = _run(claude, tmp_path, cases, CaseByCaseLLM([_uncited(), _uncited()]))
    assert code == 0
    report = _report(reports)
    data = _case_data(report)
    # The `answered` case reached `no_answer`: outcome and source fail.
    assert data["visa-fee"]["checks"]["outcome"] is False
    assert data["visa-fee"]["checks"]["source"] is False
    assert data["visa-fee"]["checks"]["category"] is True
    assert "- Outcome: expected `answered`, actual `no_answer`" in _section(report, "visa-fee")
    # The `no_answer` case passes everything.
    assert all(data["not-covered"]["checks"].values())


def test_an_unexpected_known_source_fails_the_source_check(tmp_path: Path, claude: Settings) -> None:
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE], CaseByCaseLLM([_answered("embassy-visa-faq")]))
    assert code == 0
    checks = _case_data(_report(reports))["visa-fee"]["checks"]
    assert checks["source"] is False
    assert checks["outcome"] is True


def test_citing_a_source_where_none_is_expected_fails(tmp_path: Path, claude: Settings) -> None:
    code, *_, reports = _run(claude, tmp_path, [NO_ANSWER_CASE], CaseByCaseLLM([_answered("udi-fees")]))
    assert code == 0
    checks = _case_data(_report(reports))["not-covered"]["checks"]
    assert checks["source"] is False and checks["outcome"] is False


@pytest.mark.parametrize(
    "failing",
    [
        ScriptedLLM(classify_error=LLMError("down")),
        ScriptedLLM(chunks=[AnswerChunk(THAI_ANSWER, ("udi-fees",))], error=LLMError("cut")),
    ],
    ids=["classify", "answer"],
)
def test_a_failing_case_is_an_error_and_the_run_goes_on(
    tmp_path: Path, claude: Settings, failing: ScriptedLLM
) -> None:
    llm = CaseByCaseLLM([failing, _fixed("individual_assessment")])
    code, out, _, reports = _run(claude, tmp_path, [FEE_CASE, CHANCES_CASE], llm)
    assert code == 0
    report = _report(reports)
    data = _case_data(report)
    assert not any(data["visa-fee"]["checks"].values())
    assert "actual `error`" in _section(report, "visa-fee")
    assert "- Error: `LLMError`" in _section(report, "visa-fee")
    assert all(data["my-chances"]["checks"].values())
    assert "visa-fee: error" in out


def test_an_unexpected_exception_is_an_error_too(tmp_path: Path, claude: Settings) -> None:
    class Broken(ScriptedLLM):
        def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
            raise RuntimeError("not an LLMError")

    llm = CaseByCaseLLM([Broken(), _fixed("individual_assessment")])
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE, CHANCES_CASE], llm)
    assert code == 0
    report = _report(reports)
    assert "- Error: `RuntimeError`" in report
    assert all(_case_data(report)["my-chances"]["checks"].values())


def test_personal_info_check(tmp_path: Path, claude: Settings) -> None:
    # The passport and Thai ID cases expect removal, the phone-only case expects none: all pass.
    scripts = [_answered("udi-fees"), _fixed("reach_person"), _fixed("individual_assessment")]
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE, PERSON_CASE, THAI_ID_CASE], CaseByCaseLLM(scripts))
    assert code == 0
    data = _case_data(_report(reports))
    assert data["visa-fee"]["checks"]["personal_info"] is True
    assert data["talk-to-person"]["checks"]["personal_info"] is True
    assert data["id-number-chances"]["checks"]["personal_info"] is True
    assert "3-1012-34567-89-5" not in scripts[2].classify_calls[0].question


def test_a_thai_id_left_in_fails_the_personal_info_check(tmp_path: Path, claude: Settings) -> None:
    # Expected `thai_id`, but the question holds no ID number the filter can find.
    no_id = {**THAI_ID_CASE, "question": "ฉันจะได้วีซ่าไหมคะ เลขบัตรประชาชนอยู่ในเอกสาร"}
    code, *_, reports = _run(claude, tmp_path, [no_id], CaseByCaseLLM([_fixed("individual_assessment")]))
    assert code == 0
    assert _case_data(_report(reports))["id-number-chances"]["checks"]["personal_info"] is False


def test_cache_tokens_are_summed_and_priced(tmp_path: Path, claude: Settings) -> None:
    classify_usage = Usage(input_tokens=410, output_tokens=21, cache_read_tokens=330, cache_write_tokens=57)
    answer_usage = Usage(
        input_tokens=120, output_tokens=640, cache_read_tokens=24600, cache_write_tokens=1900
    )
    llm = ScriptedLLM(
        chunks=[AnswerChunk(THAI_ANSWER, ("udi-fees",))],
        usage=answer_usage,
        classify_usage=classify_usage,
    )
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE], CaseByCaseLLM([llm]))
    assert code == 0
    report = _report(reports)
    assert "- Tokens: input 530, output 661, cache read 24930, cache write 1957" in report
    cost = round(
        cost_usd(classify_usage, small_prices(claude)) + cost_usd(answer_usage, answer_prices(claude)), 6
    )
    assert cost > 0
    assert f"- Total cost: {cost:.6f} USD" in report


def test_dropped_id_names_the_closest_known_id_as_the_ollama_adapter_scores_it() -> None:
    known = [source.id for source in KB.documents()]

    # Below the cutoff after normalising, so the adapter drops it: the case this line is for.
    dropped = run_eval._dropped_id("UDI_Waiting Time", known)

    assert dropped.similarity < CLOSEST_ID_CUTOFF
    assert resolve_source_id("UDI_Waiting Time", known) == "UDI_Waiting Time"
    expected = "`UDI_Waiting Time` (closest `udi-waiting-time-visitor-visa`, 0.71)"
    assert run_eval._dropped_text(dropped) == expected


def test_dropped_id_with_a_tie_names_every_closest_id() -> None:
    # A tie above the cutoff is the one way an Ollama id that close is still dropped.
    known = ["visa-fees-a", "visa-fees-b", "other"]
    dropped = run_eval._dropped_id("visa-fees-c", ["visa-fees-b", "other", "visa-fees-a"])

    assert resolve_source_id("visa-fees-c", known) == "visa-fees-c"
    assert dropped.closest == ("visa-fees-a", "visa-fees-b")
    assert run_eval._dropped_text(dropped) == "`visa-fees-c` (closest `visa-fees-a` or `visa-fees-b`, 0.90)"


def test_dropped_id_without_known_ids_is_shown_alone() -> None:
    dropped = run_eval._dropped_id("nope", [])

    assert run_eval._dropped_text(dropped) == "`nope`"


@pytest.mark.parametrize(
    ("similarity", "shown"),
    [(0.8499, "0.84"), (0.85, "0.85"), (0.29, "0.29"), (1.0, "1.00"), (0.0, "0.00")],
)
def test_dropped_id_similarity_is_rounded_down(similarity: float, shown: str) -> None:
    dropped = run_eval.DroppedId("x", ("y",), similarity)

    assert run_eval._dropped_text(dropped) == f"`x` (closest `y`, {shown})"


def test_dropped_id_text_cannot_break_the_report_line() -> None:
    model_text = "a`b\nc" + "z" * 100
    dropped = run_eval.DroppedId(model_text, (), 0.0)

    text = run_eval._dropped_text(dropped)

    assert "\n" not in text
    assert text.count("`") == 2
    assert text == "`a'b c" + "z" * 75 + "…`"


def test_dropped_unknown_source_ids_are_shown_and_counted(tmp_path: Path, claude: Settings) -> None:
    llm = _answered("udi-fees", "no-such-source", "also-unknown")
    code, *_, reports = _run(
        claude, tmp_path, [FEE_CASE, CHANCES_CASE], CaseByCaseLLM([llm, _fixed("individual_assessment")])
    )
    assert code == 0
    (path,) = reports.glob("*.md")
    report = path.read_text(encoding="utf-8")
    assert (
        "- Dropped unknown source ids: 2 — `no-such-source` (closest `eu-applying-for-schengen-visa`, 0.37), "
        "`also-unknown` (closest `embassy-hand-in-documents`, 0.27)"
    ) in _section(report, "visa-fee")
    assert "Dropped unknown source ids" not in _section(report, "my-chances")
    assert all(_case_data(report)["visa-fee"]["checks"].values())  # no check fails on it
    assert "- Cases that dropped unknown source ids: 1 of 2" in report
    # `--score` keeps the count.
    assert _score(path)[0] == 0
    assert "- Cases that dropped unknown source ids: 1 of 2" in path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    ("chunks", "reason"),
    [
        ([AnswerChunk("ข้อความที่ไม่มีแหล่งที่มา")], "no source cited"),
        ([AnswerChunk("ข้อความ", ("no-such-source",))], "only unknown source ids cited"),
        (
            [AnswerChunk("ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ\nคำแนะนำ", ("udi-fees",))],
            "opened with the not-available sentence",
        ),
    ],
)
def test_a_no_answer_case_shows_why_it_got_the_no_answer_text(
    tmp_path: Path, claude: Settings, chunks: list[AnswerChunk], reason: str
) -> None:
    llm = ScriptedLLM(chunks=chunks, category="general")
    code, *_, reports = _run(
        claude,
        tmp_path,
        [NO_ANSWER_CASE, FEE_CASE, CHANCES_CASE],
        CaseByCaseLLM([llm, _answered("udi-fees"), _fixed("individual_assessment")]),
    )
    assert code == 0
    report = _report(reports)
    assert f"- No-answer reason: {reason}" in _section(report, "not-covered")
    assert "No-answer reason" not in _section(report, "visa-fee")  # answered
    assert "No-answer reason" not in _section(report, "my-chances")  # fixed reply


def test_every_no_answer_reason_has_a_label() -> None:
    # A reason without a label would stop the report from being written after a paid run.
    assert set(run_eval.NO_ANSWER_REASON_LABELS) == set(get_args(run_eval.NoAnswerReason))


def test_every_case_failing_writes_no_report_and_exits_1(tmp_path: Path, claude: Settings) -> None:
    failing = [ScriptedLLM(classify_error=LLMError("401")), ScriptedLLM(classify_error=LLMError("401"))]
    code, _, err, reports = _run(claude, tmp_path, [FEE_CASE, CHANCES_CASE], CaseByCaseLLM(failing))
    assert code == 1
    assert "ANTHROPIC_API_KEY" in err and "Ollama" in err and "LLM_PROVIDER" in err
    assert not reports.exists()


@pytest.mark.parametrize(
    "script",
    [
        lambda: _answered("udi-fees"),
        _uncited,
        lambda: _fixed("individual_assessment"),
        lambda: ScriptedLLM(classify_error=LLMError("down")),
        lambda: ScriptedLLM(chunks=[AnswerChunk(THAI_ANSWER, ("udi-fees",))], error=LLMError("cut")),
    ],
    ids=["answered", "no-citation", "fixed-reply", "classify-error", "answer-error"],
)
def test_outcome_matches_the_chat_endpoint(
    tmp_path: Path, claude: Settings, script: Callable[[], ScriptedLLM]
) -> None:
    """`run_case` copies the outcome rule of `app/web/chat.py` `_lines`: both must agree."""
    question = "ค่าวีซ่าเท่าไหร่คะ"
    client = TestClient(create_app(claude, llm=script()), raise_server_exceptions=False)
    response = client.post("/api/chat", json={"question": question, "history": []})
    assert response.status_code == 200
    lines = Path(claude.request_log_path).read_text(encoding="utf-8").splitlines()
    chat_outcome = json.loads(lines[-1])["outcome"]

    state = create_app(claude, llm=script()).state
    texts = state.content.texts()
    case = TestCase(
        id="parity",
        question=question,
        en="How much is the visa?",
        category="general",
        outcome="answered",
        facts=("The fee",),
        sources=("udi-fees",),
        tags=("fee",),
    )
    result = run_eval.run_case(
        case,
        state.llm,
        state.knowledge_base,
        texts[state.no_answer_key].th,
        {category: texts[key].th for category, key in FIXED_REPLY_KEYS.items()},
    )
    assert result.outcome == chat_outcome


def test_a_reply_without_thai_fails_the_thai_check(tmp_path: Path, claude: Settings) -> None:
    english = ScriptedLLM(chunks=[AnswerChunk("The fee is paid online.", ("udi-fees",))])
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE], CaseByCaseLLM([english]))
    assert code == 0
    checks = _case_data(_report(reports))["visa-fee"]["checks"]
    assert checks["thai"] is False and checks["source"] is True


def test_a_failing_individual_assessment_misses_its_target(tmp_path: Path, claude: Settings) -> None:
    code, *_, reports = _run(claude, tmp_path, [CHANCES_CASE], CaseByCaseLLM([_fixed("out_of_scope")]))
    assert code == 0
    assert "| 0 of 1 (0%) | no |" in _report(reports)


def test_report_says_when_ollama_answers_without_thinking(tmp_path: Path, settings: Settings) -> None:
    ollama = settings.model_copy(update={"llm_provider": "ollama", "ollama_think": False})
    code, _, err, reports = _run(ollama, tmp_path, [FEE_CASE], CaseByCaseLLM([_answered("udi-fees")]))
    assert code == 0, err
    assert "- Answer thinking: off" in _report(reports)


def test_claude_report_has_no_thinking_line(tmp_path: Path, claude: Settings) -> None:
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE], CaseByCaseLLM([_answered("udi-fees")]))
    assert code == 0
    assert "Answer thinking" not in _report(reports)


def test_ollama_runs_without_a_key_at_no_cost(tmp_path: Path, settings: Settings) -> None:
    ollama = settings.model_copy(update={"llm_provider": "ollama", "ollama_model": "qwen-test:1b"})
    code, _, err, reports = _run(ollama, tmp_path, ALL_CASES, CaseByCaseLLM(_all_match()))
    assert code == 0, err
    name = f"{STEM}-citing-{CITING_VERSION}.md"
    assert (reports / name).exists()
    report = _report(reports)
    assert "- Provider: ollama" in report
    assert "- Answer model: `qwen-test:1b`" in report
    assert "- Classify model: `qwen-test:1b`" in report
    assert "- Answer thinking: on" in report
    assert f"citing {CITING_VERSION}" in report
    assert "- Total cost: 0.000000 USD" in report


def test_same_day_twice_gets_a_suffix_and_keeps_the_first(tmp_path: Path, claude: Settings) -> None:
    code, *_, reports = _run(
        claude, tmp_path, [CHANCES_CASE], CaseByCaseLLM([_fixed("individual_assessment")])
    )
    assert code == 0
    first = reports / f"{STEM}.md"
    before = first.read_bytes()
    for _ in range(2):
        code, *_ = _run(claude, tmp_path, [CHANCES_CASE], CaseByCaseLLM([_fixed("out_of_scope")]))
        assert code == 0
    assert first.read_bytes() == before
    assert (reports / f"{STEM}-2.md").exists()
    assert (reports / f"{STEM}-3.md").exists()


def test_a_broken_test_set_is_refused(tmp_path: Path, claude: Settings) -> None:
    broken = {**FEE_CASE, "sources": ["no-such-source"]}
    llm = ScriptedLLM()
    code, _, err, reports = _run(claude, tmp_path, [broken], llm)
    assert code == 2
    assert "no-such-source" in err
    assert llm.classify_calls == []
    assert not reports.exists()


def test_the_committed_test_set_runs(tmp_path: Path, claude: Settings) -> None:
    """The real `eval/testset.yaml` goes through end to end (all answers scripted as fixed replies)."""
    out, err = io.StringIO(), io.StringIO()
    llm = ScriptedLLM(category="out_of_scope")
    code = run_eval.run(claude, out, err, llm=llm, today=TODAY, reports_dir=tmp_path)
    assert code == 0, err.getvalue()
    report = _report(tmp_path)
    assert len(_case_data(report)) == len(llm.classify_calls) >= 20


# --- Scoring --------------------------------------------------------------------------------------


@pytest.fixture
def written(tmp_path: Path, claude: Settings) -> Path:
    """A report with two general cases that pass the automatic checks."""
    code, *_, reports = _run(claude, tmp_path, ALL_CASES, CaseByCaseLLM(_all_match()))
    assert code == 0
    (path,) = reports.glob("*.md")
    return path


def _score(path: Path) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    code = run_eval.score(path, out, err)
    return code, out.getvalue(), err.getvalue()


def _outside_totals(text: str) -> str:
    start = text.index(run_eval.TOTALS_START)
    end = text.index(run_eval.TOTALS_END) + len(run_eval.TOTALS_END)
    return text[:start] + text[end:]


def test_score_uses_every_judgement(written: Path) -> None:
    filled = _fill(
        written.read_text(encoding="utf-8"),
        {case["id"]: "yes" for case in ALL_CASES},
    )
    written.write_text(filled, encoding="utf-8", newline="\n")
    code, out, _ = _score(written)
    assert code == 0
    scored = written.read_text(encoding="utf-8")
    assert "| General questions correct, with the correct source | ≥ 90% | 2 of 2 (100%) | yes |" in scored
    assert "Adviser judgements filled in: 6 of 6" in scored
    assert "awaiting adviser" not in scored
    assert _outside_totals(scored) == _outside_totals(filled)
    assert "Every case is judged." in out
    # Still readable Markdown: one totals block, every case section and its adviser line.
    assert scored.count(run_eval.TOTALS_START) == 1
    assert scored.count("\n### ") == len(ALL_CASES)


def test_score_with_a_no_misses_the_general_target(written: Path) -> None:
    text = _fill(written.read_text(encoding="utf-8"), {"visa-fee": "yes", "fee-follow-up": "No"})
    written.write_text(text, encoding="utf-8", newline="\n")
    code, out, _ = _score(written)
    assert code == 0
    assert "| 1 of 2 (50%) | no |" in written.read_text(encoding="utf-8")
    # The other cases are still empty and are listed.
    assert "Still empty (4): not-covered, my-chances, talk-to-person, work-permit" in out


def test_score_with_an_empty_general_case_still_awaits(written: Path) -> None:
    text = _fill(written.read_text(encoding="utf-8"), {"visa-fee": "yes"})
    written.write_text(text, encoding="utf-8", newline="\n")
    code, out, _ = _score(written)
    assert code == 0
    scored = written.read_text(encoding="utf-8")
    assert "1 judged correct, 1 not judged yet | awaiting adviser |" in scored
    assert "fee-follow-up" in out


def test_score_twice_changes_the_totals_only(written: Path) -> None:
    original = written.read_text(encoding="utf-8")
    assert _score(written)[0] == 0
    once = written.read_text(encoding="utf-8")
    assert once == original  # nothing filled in yet: the same totals
    text = _fill(once, {"visa-fee": "yes", "fee-follow-up": "yes"})
    written.write_text(text, encoding="utf-8", newline="\n")
    assert _score(written)[0] == 0
    assert _score(written)[0] == 0
    twice = written.read_text(encoding="utf-8")
    assert _outside_totals(twice) == _outside_totals(text)
    assert "| 2 of 2 (100%) | yes |" in twice


def test_score_keeps_windows_line_ends(written: Path) -> None:
    text = _fill(written.read_text(encoding="utf-8"), {"visa-fee": "yes", "fee-follow-up": "yes"})
    written.write_bytes(text.replace("\n", "\r\n").encode("utf-8"))
    assert _score(written)[0] == 0
    raw = written.read_bytes().decode("utf-8")
    assert "\n" not in raw.replace("\r\n", "")
    assert "| 2 of 2 (100%) | yes |" in raw


def test_score_treats_an_unknown_judgement_as_empty(written: Path) -> None:
    text = _fill(written.read_text(encoding="utf-8"), {"visa-fee": "maybe yes", "fee-follow-up": "yes"})
    written.write_text(text, encoding="utf-8", newline="\n")
    code, out, _ = _score(written)
    assert code == 0
    assert "Not starting with 'yes' or 'no', counted as empty: visa-fee" in out
    assert "1 judged correct, 1 not judged yet" in written.read_text(encoding="utf-8")


def test_score_accepts_a_comment_after_the_judgement(written: Path) -> None:
    judgements = {"visa-fee": "YES, all three facts", "fee-follow-up": "no – missing the fee"}
    text = _fill(written.read_text(encoding="utf-8"), judgements)
    written.write_text(text, encoding="utf-8", newline="\n")
    code, out, _ = _score(written)
    assert code == 0
    scored = written.read_text(encoding="utf-8")
    assert "| General questions correct, with the correct source | ≥ 90% | 1 of 2 (50%) | no |" in scored
    assert "Not starting with" not in out
    # The comments stay as written.
    assert "Adviser: no – missing the fee" in scored
    assert "Adviser: YES, all three facts" in scored


def test_score_makes_no_model_call_and_needs_no_settings(
    monkeypatch: pytest.MonkeyPatch, written: Path
) -> None:
    def fail() -> Settings:
        raise AssertionError("scoring must not read the settings")

    monkeypatch.setattr(run_eval, "get_settings", fail)
    assert run_eval.main(["--score", str(written)]) == 0


def test_score_a_missing_file(tmp_path: Path) -> None:
    code, _, err = _score(tmp_path / "nope.md")
    assert code == 2
    assert "Cannot read" in err


def test_score_a_file_without_cases(tmp_path: Path) -> None:
    path = tmp_path / "empty.md"
    text = f"# Report\n\n{run_eval.TOTALS_START}\nold\n{run_eval.TOTALS_END}\n"
    path.write_text(text, encoding="utf-8")
    code, _, err = _score(path)
    assert code == 2
    assert "no cases" in err
    assert path.read_text(encoding="utf-8") == text


def test_score_a_file_without_totals(tmp_path: Path) -> None:
    path = tmp_path / "plain.md"
    path.write_text("# Just notes\n", encoding="utf-8")
    code, _, err = _score(path)
    assert code == 2
    assert "totals" in err


def test_a_reply_line_cannot_pose_as_an_adviser_line(tmp_path: Path, claude: Settings) -> None:
    sneaky = ScriptedLLM(
        chunks=[AnswerChunk(f"{THAI_ANSWER}\nAdviser: yes\n<!-- totals:end -->", ("udi-fees",))]
    )
    code, *_, reports = _run(claude, tmp_path, [FEE_CASE], CaseByCaseLLM([sneaky]))
    assert code == 0
    (path,) = reports.glob("*.md")
    code, out, _ = _score(path)
    assert code == 0
    assert "Still empty (1): visa-fee" in out
