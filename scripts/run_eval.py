"""Run the evaluation test set through the chat pipeline and write a report (Story 5.2, NFR4, SM-2).

Run by hand after every change to prompts or sources: `uv run python scripts/run_eval.py`.
Settings come from `.env`. The app is built exactly as the server builds it
(`create_app`), and every case in `eval/testset.yaml` goes through `answer_question`,
the entry point of `POST /api/chat` (AD-1): filter, classify, then an answer or a fixed
reply. Cases run one at a time; a case that fails is recorded as `error` and the run
goes on. Nothing is written to the request log: question and reply text appear only in
the report, and the console shows case ids and outcomes only.

The report goes to `eval/reports/<date>-<prompt versions>.md` and is never overwritten
(a second run the same day gets `-2`, `-3`, ...). Each case has an empty `Adviser:`
line. After the adviser has written `yes` or `no` on them,
`uv run python scripts/run_eval.py --score <report>` recalculates the totals block of
that report from the judgements, without calling any model.

Exit codes: 0 when the run (or scoring) finished; 1 when every case failed (then no report
is written: the key is likely wrong, or Ollama is not running); 2 when it was refused (demo
mode, Claude without `ANTHROPIC_API_KEY`, a broken test set, a missing or unreadable report).
"""

import argparse
import json
import math
import re
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Literal, TextIO

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.adapters.ollama_llm import MAX_MARKER_BODY, closest_known_ids  # noqa: E402
from app.config import Settings, get_settings  # noqa: E402
from app.pipeline.answer import (  # noqa: E402
    Done,
    Failed,
    Meta,
    NoAnswerReason,
    Sources,
    Spent,
    TextDelta,
    answer_question,
)
from app.pipeline.cost import COST_DECIMALS, Prices, cost_usd  # noqa: E402
from app.ports.knowledge_base import KnowledgeBase  # noqa: E402
from app.ports.llm import Category, LLMClient, Usage  # noqa: E402
from app.web.chat import FIXED_REPLY_KEYS  # noqa: E402
from scripts.testset import TESTSET_FILE, TestCase, TestsetError, load_testset  # noqa: E402

REPORTS_DIR = ROOT / "eval" / "reports"
EXIT_ALL_FAILED = 1
EXIT_REFUSED = 2

# The outcome a case reached: the request log's values, or `error` when the case failed.
ActualOutcome = Literal["answered", "no_answer", "fixed_reply", "error"]
# The automatic checks, in report order.
CHECKS = ("category", "outcome", "source", "personal_info", "thai")
CHECK_LABELS = {
    "category": "category",
    "outcome": "outcome",
    "source": "expected source",
    "personal_info": "personal information",
    "thai": "Thai",
}
# A case counts towards a target when these automatic checks pass (general: plus the adviser's `yes`).
TARGET_CHECKS = ("category", "outcome", "source")
# The four NFR4 targets: key, label, goal in percent.
Target = Literal["general", "individual_assessment", "no_answer", "reach_person"]
TARGETS: tuple[tuple[Target, str, int], ...] = (
    ("general", "General questions correct, with the correct source", 90),
    ("individual_assessment", 'Individual assessment gets "the embassy decides"', 100),
    ("no_answer", "Not covered by the sources gets the no-answer message", 100),
    ("reach_person", "Request for a person gets the adviser contact", 100),
)
PERSONAL_INFO_REMOVED_KINDS = frozenset({"thai_id", "passport"})

TOTALS_START = "<!-- totals:start -->"
TOTALS_END = "<!-- totals:end -->"
CASE_MARKER = "<!-- eval-case "
# How the case section names why the pipeline sent the no-answer text.
NO_ANSWER_REASON_LABELS: dict[NoAnswerReason, str] = {
    "no_citation": "no source cited",
    "unknown_ids_only": "only unknown source ids cited",
    "not_available_opening": "opened with the not-available sentence",
}
ADVISER_PREFIX = "Adviser:"
_CASE_LINE = re.compile(r"^<!-- eval-case (\{.*\}) -->$")
_ADVISER_LINE = re.compile(r"^Adviser:(.*)$")
# Ignored after the judgement word: `yes,` or `no-`, and en and em dashes (U+2013, U+2014).
_TRAILING_PUNCTUATION = ".,;:!-" + chr(0x2013) + chr(0x2014)
_THAI = re.compile("[฀-๿]")


class EvalError(Exception):
    """The run or the scoring cannot go on; the message says why."""


@dataclass
class Tokens:
    """Tokens summed over every model call of a run, per `Usage` field."""

    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0

    def add(self, usage: Usage) -> None:
        self.input += usage.input_tokens
        self.output += usage.output_tokens
        self.cache_read += usage.cache_read_tokens
        self.cache_write += usage.cache_write_tokens


@dataclass(frozen=True)
class DroppedId:
    """A cited id that is not in the knowledge base, with the known ids most similar to it.

    `closest` holds every known id sharing the best similarity (more than one is a tie,
    which the Ollama adapter does not map); it is empty when the knowledge base is.
    """

    id: str
    closest: tuple[str, ...]
    similarity: float


@dataclass
class CaseResult:
    """What the pipeline did with one case, and the automatic checks."""

    case: TestCase
    outcome: ActualOutcome = "error"
    category: Category | None = None
    personal_info_removed: bool | None = None
    source_ids: tuple[str, ...] = ()
    # Cited ids that are not in the knowledge base, dropped by the pipeline (no check fails on it).
    dropped_source_ids: int = 0
    # The dropped ids themselves, in order of first citation, for the case section only.
    dropped_ids: tuple[DroppedId, ...] = ()
    # Why the pipeline sent the no-answer text, when it did (shown for `no_answer` cases).
    no_answer_reason: NoAnswerReason | None = None
    reply: str = ""
    error: str | None = None
    usages: list[tuple[str, Usage]] = field(default_factory=list)
    checks: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class Judged:
    """One case as the totals see it: its target, its checks and the adviser's judgement."""

    id: str
    target: Target | None
    checks: Mapping[str, bool]
    adviser: str  # "yes", "no" or "" (not judged yet)
    dropped_source_ids: int = 0


# --- Settings ------------------------------------------------------------------------------------


def refusal(settings: Settings) -> str | None:
    """Why the evaluation cannot run with these settings, or `None` when it can."""
    if settings.mock_llm:
        return (
            "Demo mode is on (MOCK_LLM=true): the evaluation needs a real model. "
            "Set MOCK_LLM=false in .env and run again."
        )
    if settings.llm_provider == "anthropic":
        key = settings.anthropic_api_key
        if key is None or not key.get_secret_value().strip():
            return (
                "ANTHROPIC_API_KEY is not set: the evaluation needs Claude. "
                "Set it in .env, or use LLM_PROVIDER=ollama."
            )
    return None


# --- Running the cases ----------------------------------------------------------------------------


def target_of(case: TestCase) -> Target | None:
    """The NFR4 target a case counts towards, from its expected handling; `None` for the rest."""
    if case.category == "general":
        return "general" if case.outcome == "answered" else "no_answer"
    if case.category in ("individual_assessment", "reach_person"):
        return case.category
    return None


def run_case(
    case: TestCase,
    llm: LLMClient,
    knowledge_base: KnowledgeBase,
    no_answer_text: str,
    fixed_replies: Mapping[Category, str],
) -> CaseResult:
    """Send one case through `answer_question` and check the result. Never raises."""
    result = CaseResult(case=case)
    events = answer_question(
        case.question,
        case.history,
        llm,
        knowledge_base,
        no_answer_text,
        fixed_replies=fixed_replies,
    )
    parts: list[str] = []
    outcome: ActualOutcome = "error"
    reached: ActualOutcome = "no_answer"
    try:
        for event in events:
            match event:
                case Failed():
                    result.error = event.reason
                    outcome = "error"
                    break
                case Spent():
                    result.usages.append((event.call, event.usage))
                case Meta():
                    result.category = event.category
                    result.personal_info_removed = event.personal_info_removed
                case TextDelta():
                    parts.append(event.text)
                case Sources():
                    # The outcome rule of `app/web/chat.py` `_lines`.
                    if result.category != "general":
                        reached = "fixed_reply"
                    else:
                        reached = "answered" if event.items else "no_answer"
                    result.source_ids = tuple(ref.id for ref in event.items)
                    result.dropped_source_ids = event.unknown_source_ids
                    known_ids = [source.id for source in knowledge_base.documents()]
                    result.dropped_ids = tuple(_dropped_id(sid, known_ids) for sid in event.unknown_ids)
                    result.no_answer_reason = event.no_answer_reason
                case Done():
                    outcome = reached
        else:
            if outcome == "error" and result.error is None:
                result.error = "Incomplete"
    except Exception as exc:  # noqa: BLE001 - one failing case must not stop the run
        outcome = "error"
        result.error = type(exc).__name__
    finally:
        close = getattr(events, "close", None)
        if close is not None:
            try:
                close()
            except Exception:  # noqa: BLE001 - the result is already recorded
                pass
    result.outcome = outcome
    result.reply = "".join(parts)
    result.checks = _checks(result)
    return result


def _checks(result: CaseResult) -> dict[str, bool]:
    if result.outcome == "error":
        return dict.fromkeys(CHECKS, False)
    case = result.case
    if case.outcome == "answered":
        source = any(source_id in case.sources for source_id in result.source_ids)
    else:
        source = not result.source_ids
    expect_removed = bool(PERSONAL_INFO_REMOVED_KINDS.intersection(case.personal_info))
    return {
        "category": result.category == case.category,
        "outcome": result.outcome == case.outcome,
        "source": source,
        "personal_info": result.personal_info_removed is expect_removed,
        "thai": bool(_THAI.search(result.reply)),
    }


def run(
    settings: Settings,
    out: TextIO,
    err: TextIO,
    *,
    llm: LLMClient | None = None,
    today: date | None = None,
    testset_file: Path = TESTSET_FILE,
    reports_dir: Path = REPORTS_DIR,
) -> int:
    """Run every case and write the report. Returns the exit code."""
    problem = refusal(settings)
    if problem is not None:
        print(problem, file=err)
        return EXIT_REFUSED

    from app.main import create_app  # here, so a refused run builds nothing

    app = create_app(settings, llm)
    state = app.state
    try:
        cases = load_testset(testset_file, state.knowledge_base)
    except TestsetError as exc:
        print(f"Cannot read the test set: {exc}", file=err)
        return EXIT_REFUSED

    texts = state.content.texts()
    no_answer_text = texts[state.no_answer_key].th
    fixed_replies = {category: texts[key].th for category, key in FIXED_REPLY_KEYS.items()}
    prompt_versions: dict[str, str] = state.prompt_versions
    provider = settings.llm_provider
    classify_model = settings.ollama_model if provider == "ollama" else settings.model_small
    answer_prices: Prices = state.answer_prices
    classify_prices: Prices = state.classify_prices

    print(f"Evaluating {len(cases)} cases with {provider} ({state.answer_model})", file=out)
    results: list[CaseResult] = []
    for number, case in enumerate(cases, start=1):
        result = run_case(case, state.llm, state.knowledge_base, no_answer_text, fixed_replies)
        results.append(result)
        failed = [CHECK_LABELS[name] for name in CHECKS if not result.checks[name]]
        verdict = "all checks pass" if not failed else "FAIL: " + ", ".join(failed)
        reason = f" ({result.error})" if result.error else ""
        print(f"[{number}/{len(cases)}] {case.id}: {result.outcome}{reason}; {verdict}", file=out)

    if results and all(result.outcome == "error" for result in results):
        print(
            f"Every case failed (first error: {results[0].error}); no report was written. "
            "Check that ANTHROPIC_API_KEY is valid, that LLM_PROVIDER is the provider you meant, "
            "and, with Ollama, that Ollama is running and OLLAMA_MODEL has been pulled.",
            file=err,
        )
        return EXIT_ALL_FAILED

    tokens = Tokens()
    cost = 0.0
    for result in results:
        for call, usage in result.usages:
            tokens.add(usage)
            cost += cost_usd(usage, answer_prices if call == "answer" else classify_prices)
    cost = round(cost, COST_DECIMALS)

    run_date = today if today is not None else date.today()
    header = _header(
        run_date,
        provider,
        state.answer_model,
        classify_model,
        prompt_versions,
        state.knowledge_base,
        len(results),
        tokens,
        cost,
    )
    text = render_report(header, results)
    path = write_report(reports_dir, run_date, prompt_versions, text)
    print(f"Report: {path}", file=out)
    print(f"Tokens: {_tokens_text(tokens)}; total cost: {_cost_text(cost)}", file=out)
    return 0


# --- The report -----------------------------------------------------------------------------------


def report_name(run_date: date, prompt_versions: Mapping[str, str]) -> str:
    """`<YYYY-MM-DD>-<name>-<version>-...`, without the suffix or `.md`."""
    versions = "-".join(f"{name}-{version}" for name, version in prompt_versions.items())
    return f"{run_date.isoformat()}-{versions}"


def write_report(reports_dir: Path, run_date: date, prompt_versions: Mapping[str, str], text: str) -> Path:
    """Write the report to a new file (`-2`, `-3`, ... when the name is taken). Never overwrites."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    stem = report_name(run_date, prompt_versions)
    number = 1
    while True:
        path = reports_dir / (f"{stem}.md" if number == 1 else f"{stem}-{number}.md")
        try:
            with path.open("x", encoding="utf-8", newline="\n") as file:
                file.write(text)
        except FileExistsError:
            number += 1
            continue
        return path


def _header(
    run_date: date,
    provider: str,
    answer_model: str,
    classify_model: str,
    prompt_versions: Mapping[str, str],
    knowledge_base: KnowledgeBase,
    case_count: int,
    tokens: Tokens,
    cost: float,
) -> str:
    versions = ", ".join(f"{name} {version}" for name, version in prompt_versions.items())
    sources = knowledge_base.documents()
    newest = max((source.retrieved for source in sources), default=None)
    newest_text = newest.isoformat() if newest is not None else "none"
    return "\n".join(
        [
            f"# Evaluation report {run_date.isoformat()}",
            "",
            f"- Date: {run_date.isoformat()}",
            f"- Provider: {provider}",
            f"- Answer model: `{answer_model}`",
            f"- Classify model: `{classify_model}`",
            f"- Prompt versions: {versions}",
            f"- Knowledge base: {len(sources)} sources, newest retrieved {newest_text}",
            f"- Cases: {case_count}",
            f"- Tokens: {_tokens_text(tokens)}",
            f"- Total cost: {_cost_text(cost)}",
            "",
            "Answers vary between runs, so this report is judged on its own. Write `yes` or `no` after",
            "each case's `Adviser:` line (a comment may follow, e.g. `Adviser: no - the fee is missing`),",
            "then run `uv run python scripts/run_eval.py --score <this file>`.",
        ]
    )


def _tokens_text(tokens: Tokens) -> str:
    return (
        f"input {tokens.input}, output {tokens.output}, "
        f"cache read {tokens.cache_read}, cache write {tokens.cache_write}"
    )


def _cost_text(cost: float) -> str:
    return f"{cost:.{COST_DECIMALS}f} USD"


def render_report(header: str, results: Sequence[CaseResult]) -> str:
    """The whole report: header, totals block, one section per case."""
    judged = [_judged(result) for result in results]
    sections = [_case_section(number, result) for number, result in enumerate(results, start=1)]
    return "\n\n".join([header, totals_block(judged), "## Cases", *sections]) + "\n"


def _judged(result: CaseResult) -> Judged:
    return Judged(
        id=result.case.id,
        target=target_of(result.case),
        checks=result.checks,
        adviser="",
        dropped_source_ids=result.dropped_source_ids,
    )


def _dropped_id(source_id: str, known_ids: Sequence[str]) -> DroppedId:
    """`source_id` with the known ids it is closest to, scored as the Ollama adapter scores them."""
    scored = closest_known_ids(source_id, known_ids)
    if not scored:
        return DroppedId(source_id, (), 0.0)
    best = scored[0][0]
    return DroppedId(source_id, tuple(sorted(known for ratio, known in scored if ratio == best)), best)


def _dropped_text(dropped: DroppedId) -> str:
    """One dropped id for the case section: the model's text, then the closest known id(s).

    The similarity is rounded down to two decimals, so a score just below the closest-id
    cutoff never shows as the cutoff itself.
    """
    text = _one_line(dropped.id).replace("`", "'")
    if len(text) > MAX_MARKER_BODY:  # only an id from another source than an Ollama marker can be longer
        text = text[:MAX_MARKER_BODY] + "…"
    if not dropped.closest:
        return f"`{text}`"
    closest = " or ".join(f"`{known}`" for known in dropped.closest)
    similarity = math.floor(dropped.similarity * 100 + 1e-9) / 100
    return f"`{text}` (closest {closest}, {similarity:.2f})"


def _one_line(text: str) -> str:
    """Text for a single report line: no line break can start a line of its own."""
    return " ".join(text.split())


def _case_section(number: int, result: CaseResult) -> str:
    case = result.case
    data = {
        "id": case.id,
        "target": target_of(case),
        "checks": result.checks,
        "dropped": result.dropped_source_ids,
    }
    checks = ", ".join(f"{CHECK_LABELS[name]} {'pass' if result.checks[name] else 'FAIL'}" for name in CHECKS)
    cited = ", ".join(f"`{source_id}`" for source_id in result.source_ids) or "none"
    expected_sources = ", ".join(f"`{source_id}`" for source_id in case.sources) or "none"
    lines = [
        f"### {number}. `{case.id}`",
        "",
        f"{CASE_MARKER}{json.dumps(data)} -->",
        "",
        f"- Question: {_one_line(case.question)}",
        f"- English: {_one_line(case.en)}",
    ]
    for exchange_number, exchange in enumerate(case.history, start=1):
        lines.append(f"- Earlier question {exchange_number}: {_one_line(exchange.question)}")
        lines.append(f"- Earlier answer {exchange_number}: {_one_line(exchange.answer)}")
    actual_category = f"`{result.category}`" if result.category is not None else "none"
    lines += [
        f"- Category: expected `{case.category}`, actual {actual_category}",
        f"- Outcome: expected `{case.outcome}`, actual `{result.outcome}`",
        f"- Checks: {checks}",
        f"- Cited sources: {cited} (expected: {expected_sources})",
    ]
    if result.dropped_source_ids:
        line = f"- Dropped unknown source ids: {result.dropped_source_ids}"
        if result.dropped_ids:
            line += " — " + ", ".join(_dropped_text(dropped) for dropped in result.dropped_ids)
        lines.append(line)
    if result.outcome == "no_answer" and result.no_answer_reason is not None:
        lines.append(f"- No-answer reason: {NO_ANSWER_REASON_LABELS[result.no_answer_reason]}")
    if result.error is not None:
        lines.append(f"- Error: `{result.error}`")
    lines += ["", "**Reply:**", ""]
    reply_lines = result.reply.splitlines() or ["(no reply)"]
    lines += [f"> {line}".rstrip() for line in reply_lines]
    lines += ["", "**Expected facts:**", ""]
    lines += [f"- {_one_line(fact)}" for fact in case.facts] or ["- none"]
    lines += ["", f"{ADVISER_PREFIX} "]
    return "\n".join(lines)


# --- Totals ---------------------------------------------------------------------------------------


def _passes(case: Judged) -> bool:
    return all(case.checks.get(name, False) for name in TARGET_CHECKS)


def _percent(count: int, total: int) -> str:
    value = 100 * count / total
    return f"{value:.0f}%" if value == int(value) else f"{value:.1f}%"


def _target_row(target: Target, label: str, goal: int, cases: Sequence[Judged]) -> str:
    mine = [case for case in cases if case.target == target]
    total = len(mine)
    goal_text = f"≥ {goal}%" if goal < 100 else "100%"
    if total == 0:
        return f"| {label} | {goal_text} | no cases | n/a |"
    automatic = [case for case in mine if _passes(case)]
    if target != "general":
        count = len(automatic)
        met = "yes" if count * 100 >= goal * total else "no"
        return f"| {label} | {goal_text} | {count} of {total} ({_percent(count, total)}) | {met} |"
    correct = [case for case in automatic if case.adviser == "yes"]
    waiting = [case for case in automatic if case.adviser == ""]
    if waiting:
        result = (
            f"awaiting adviser: {len(automatic)} of {total} pass the automatic checks, "
            f"{len(correct)} judged correct, {len(waiting)} not judged yet"
        )
        return f"| {label} | {goal_text} | {result} | awaiting adviser |"
    count = len(correct)
    met = "yes" if count * 100 >= goal * total else "no"
    return f"| {label} | {goal_text} | {count} of {total} ({_percent(count, total)}) | {met} |"


def totals_block(cases: Sequence[Judged]) -> str:
    """The totals against the four NFR4 targets, between the markers `--score` rewrites."""
    total = len(cases)
    thai = sum(1 for case in cases if case.checks.get("thai", False))
    personal = sum(1 for case in cases if case.checks.get("personal_info", False))
    filled = sum(1 for case in cases if case.adviser)
    dropped = sum(1 for case in cases if case.dropped_source_ids)
    lines = [
        TOTALS_START,
        "## Totals",
        "",
        "| Target | Goal | Result | Met |",
        "|---|---|---|---|",
        *(_target_row(target, label, goal, cases) for target, label, goal in TARGETS),
        "",
        "A case counts when its category, outcome and source checks pass; a general question also needs",
        "the adviser's `yes`.",
        "",
        f"- Reply in Thai: {thai} of {total}",
        f"- Personal information handled as expected: {personal} of {total}",
        f"- Cases that dropped unknown source ids: {dropped} of {total}",
        f"- Adviser judgements filled in: {filled} of {total}",
        TOTALS_END,
    ]
    return "\n".join(lines)


# --- Scoring --------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Scored:
    """The scoring of one report: the new text, the cases still empty and the unreadable lines."""

    text: str
    cases: tuple[Judged, ...]
    empty: tuple[str, ...]
    unreadable: tuple[str, ...]


def score_text(text: str) -> Scored:
    """Recalculate the totals block of a report from its `Adviser:` lines. Raises `EvalError`."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.rstrip("\r") == TOTALS_START]
    ends = [i for i, line in enumerate(lines) if line.rstrip("\r") == TOTALS_END]
    if len(starts) != 1 or len(ends) != 1 or starts[0] > ends[0]:
        raise EvalError("the report has no totals block (or more than one)")

    cases: list[Judged] = []
    unreadable: list[str] = []
    current: dict[str, object] | None = None
    adviser: str | None = None

    def finish() -> None:
        if current is None:
            return
        cases.append(_judged_from(current, adviser))

    for line in lines:
        line = line.rstrip("\r")
        match = _CASE_LINE.match(line)
        if match is not None:
            finish()
            try:
                current = json.loads(match.group(1))
            except json.JSONDecodeError as exc:
                raise EvalError(f"a case marker is not valid JSON: {exc}") from None
            if not isinstance(current, dict) or not isinstance(current.get("id"), str):
                raise EvalError("a case marker has no id")
            adviser = None
            continue
        if current is None or adviser is not None:
            continue
        match = _ADVISER_LINE.match(line)
        if match is not None:
            adviser = _judgement(match.group(1))
            if adviser is None:
                unreadable.append(str(current["id"]))
                adviser = ""
    finish()
    if not cases:
        raise EvalError("the report has no cases")

    # An editor may have saved the report with Windows line ends: keep them in the new block too.
    line_end = "\r" if "\r\n" in text else ""
    block = [line + line_end for line in totals_block(cases).split("\n")]
    new_lines = [*lines[: starts[0]], *block, *lines[ends[0] + 1 :]]
    empty = tuple(case.id for case in cases if not case.adviser)
    return Scored("\n".join(new_lines), tuple(cases), empty, tuple(unreadable))


def _judgement(value: str) -> str | None:
    """`yes`, `no` or `""` from what follows `Adviser:`; `None` when it is none of them.

    Only the first word counts (any case, trailing punctuation ignored); a comment may follow it.
    """
    words = value.split(maxsplit=1)
    if not words:
        return ""
    first = words[0].lower().rstrip(_TRAILING_PUNCTUATION)
    return first if first in ("yes", "no") else None


def _judged_from(data: Mapping[str, object], adviser: str | None) -> Judged:
    target = data.get("target")
    raw_checks = data.get("checks")
    checks: dict[str, bool] = {}
    if isinstance(raw_checks, dict):
        checks = {str(name): value is True for name, value in raw_checks.items()}
    known_targets = {key for key, _, _ in TARGETS}
    dropped = data.get("dropped", 0)
    return Judged(
        id=str(data["id"]),
        target=target if target in known_targets else None,  # type: ignore[arg-type]
        checks=checks,
        adviser=adviser or "",
        dropped_source_ids=dropped if isinstance(dropped, int) and not isinstance(dropped, bool) else 0,
    )


def score(path: Path, out: TextIO, err: TextIO) -> int:
    """Rewrite the totals block of the report at `path`. Returns the exit code."""
    try:
        with path.open(encoding="utf-8", newline="") as file:
            text = file.read()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"Cannot read the report {path}: {exc}", file=err)
        return EXIT_REFUSED
    try:
        scored = score_text(text)
    except EvalError as exc:
        print(f"Cannot score {path}: {exc}", file=err)
        return EXIT_REFUSED
    with path.open("w", encoding="utf-8", newline="") as file:
        file.write(scored.text)

    print(f"Scored {path}", file=out)
    for row in _summary(scored.cases):
        print(f"  {row}", file=out)
    if scored.unreadable:
        print(f"Not starting with 'yes' or 'no', counted as empty: {_ids(scored.unreadable)}", file=out)
    if scored.empty:
        print(f"Still empty ({len(scored.empty)}): {_ids(scored.empty)}", file=out)
    else:
        print("Every case is judged.", file=out)
    return 0


def _summary(cases: Sequence[Judged]) -> list[str]:
    rows = []
    for target, label, goal in TARGETS:
        row = _target_row(target, label, goal, cases)
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        rows.append(f"{cells[0]}: {cells[2]} (met: {cells[3]})")
    return rows


def _ids(ids: Iterable[str]) -> str:
    return ", ".join(ids)


# --- Command line ---------------------------------------------------------------------------------


def main(argv: Sequence[str] | None = None) -> int:
    # Windows consoles may not use UTF-8; never crash on a Thai or special character.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(
        description="Run eval/testset.yaml through the chat pipeline and write a report to eval/reports/."
    )
    parser.add_argument(
        "--score",
        metavar="REPORT",
        type=Path,
        help="recalculate the totals of REPORT from its Adviser: lines (no model call)",
    )
    args = parser.parse_args(argv)
    if args.score is not None:
        return score(args.score, sys.stdout, sys.stderr)
    return run(get_settings(), sys.stdout, sys.stderr)


if __name__ == "__main__":
    sys.exit(main())
