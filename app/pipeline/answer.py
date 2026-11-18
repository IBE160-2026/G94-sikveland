"""The answer pipeline: filter, classify, then a grounded answer or a fixed reply (AD-1, AD-5, AD-7).

Pure logic: the events here are domain values. `app/web` turns them into stream
events (AD-8); nothing here knows about HTTP, JSON or an SDK.

Order of events: one `Spent` for the classify call, one `Meta`, zero or more
`TextDelta`, one `Spent` for the answer call when the model reported its token
use, one `Sources`, then `Done`. A fixed reply has no answer call: `Spent`
(classify), `Meta`, one `TextDelta`, an empty `Sources`, `Done`. A declined
answer (zero known citations, or a held reply that opens with a not-available
sentence) has one `TextDelta` with the no-answer text, then `Spent` (answer)
when the model reported its token use, as for any answer, an empty `Sources`,
`Done`. `Failed` can come instead of any of these events,
also the first ones when the classify call fails, and is always the last one.
"""

import re
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Literal, get_args

from app.pipeline.filter import remove_personal_info
from app.ports.knowledge_base import KnowledgeBase
from app.ports.llm import Category, Exchange, LLMClient, LLMError, Usage

# The classifier sees the cleaned question and this many of the latest exchanges (AD-5).
CLASSIFY_HISTORY_EXCHANGES = 2
UNKNOWN_CATEGORY_REASON = "UnknownCategory"
_CATEGORIES: frozenset[str] = frozenset(get_args(Category))

ModelCall = Literal["classify", "answer"]

# Not-available openings (AD-7, amended 2026-11-18). A held reply whose first line
# matches is declined: the applicant gets the no-answer text, as for zero citations.
# The words come from the example sentence in `prompts/answer-citing-markers.md`
# ("ขออภัย ไม่มีข้อมูลเรื่องนี้ค่ะ") and the wording of the fixed no-answer text
# `reply-no-answer` in `content/texts.yaml` ("ขออภัย ไม่พบคำตอบ…"), plus ไม่พบข้อมูล:
# an optional ขออภัย ("sorry"), optionally with a polite particle, then the
# not-available phrase.
NOT_AVAILABLE_APOLOGY = "ขออภัย"
NOT_AVAILABLE_PARTICLES = ("นะครับ", "นะคะ", "ครับ", "ค่ะ")
NOT_AVAILABLE_PHRASES = ("ไม่มีข้อมูล", "ไม่พบข้อมูล", "ไม่พบคำตอบ")
# Zero-width characters and Markdown emphasis are ignored where they can sit in the opening.
_INVISIBLE = "\u200b\u200c\u200d\u2060\ufeff"
_GAP = rf"[\s{_INVISIBLE}*_]*"
NOT_AVAILABLE_OPENING = re.compile(
    rf"(?:{NOT_AVAILABLE_APOLOGY}{_GAP}(?:(?:{'|'.join(NOT_AVAILABLE_PARTICLES)}){_GAP})?)?"
    rf"(?:{'|'.join(NOT_AVAILABLE_PHRASES)})"
)
# "But" and "however": a first line with one of them turns to an answer and is not
# declined. แต่ counts only as a word, not in ตั้งแต่ ("since"), แต่ละ ("each") or แต่ง… ("dress", "marry").
TURN_WORD = re.compile(r"(?<!ตั้ง)แต่(?!ง|ละ)|อย่างไรก็ตาม")
# Leading whitespace, zero-width characters and Markdown marks are skipped before matching.
_LEADING = re.compile(rf"[\s{_INVISIBLE}*_#>\-]*")
_LINE_BREAK = re.compile(r"[\r\n]")
_GAP_AT_START = re.compile(_GAP)


@dataclass(frozen=True)
class Meta:
    """What the pipeline did with the question before answering it."""

    category: Category
    personal_info_removed: bool
    clean_question: str


@dataclass(frozen=True)
class TextDelta:
    """Answer text to append to what the applicant already sees. Never empty."""

    text: str


@dataclass(frozen=True)
class SourceRef:
    """A cited source, as the applicant sees it."""

    id: str
    title: str
    url: str


@dataclass(frozen=True)
class Sources:
    """Exactly the cited sources, in order of first citation, each once.

    `unknown_source_ids` counts the distinct cited ids that are not in the knowledge
    base: they were dropped. For the request log only, never shown to the applicant.
    """

    items: tuple[SourceRef, ...]
    unknown_source_ids: int = 0


@dataclass(frozen=True)
class Spent:
    """The tokens one model call used, for the request log. Never shown to the applicant.

    `call` says which call: the two are priced differently (`PRICE_SMALL_*` for
    classify, `PRICE_ANSWER_*` for the answer). Required, so no call is priced
    as the wrong model by default.
    """

    usage: Usage
    call: ModelCall


@dataclass(frozen=True)
class Done:
    """The answer is complete."""


@dataclass(frozen=True)
class Failed:
    """The answer failed; nothing follows. `reason` is a class name or a short label, never text."""

    reason: str


AnswerEvent = Meta | TextDelta | Sources | Spent | Done | Failed


def opens_with_not_available(line: str) -> bool:
    """Whether a first line is a not-available sentence that does not turn to an answer."""
    start = _LEADING.sub("", line, count=1)
    return NOT_AVAILABLE_OPENING.match(start) is not None and TURN_WORD.search(start) is None


def _held_reply_declines(text: str, *, ended: bool) -> bool | None:
    """Decide a held, cited reply: `True` to decline it, `False` to show it, `None` to hold on.

    The decision needs the whole first line, so it waits for the first line break
    or the end of the answer, but only while the text could still be a
    not-available opening: empty, already matching `NOT_AVAILABLE_OPENING`, or a
    beginning of a match of it. Any other reply is shown at once.
    """
    start = _LEADING.sub("", text, count=1)
    line_break = _LINE_BREAK.search(start)
    if line_break is not None:
        return opens_with_not_available(start[: line_break.start()])
    if ended:
        return opens_with_not_available(start)
    return None if _could_open_with_not_available(start) else False


def _could_open_with_not_available(start: str) -> bool:
    """Whether `start` matches `NOT_AVAILABLE_OPENING` or is a beginning of a match of it."""
    if NOT_AVAILABLE_OPENING.match(start):
        return True
    rest = start
    if rest.startswith(NOT_AVAILABLE_APOLOGY):
        rest = _GAP_AT_START.sub("", rest[len(NOT_AVAILABLE_APOLOGY) :], count=1)
        particle = next((p for p in NOT_AVAILABLE_PARTICLES if rest.startswith(p)), None)
        if particle is not None:
            rest = _GAP_AT_START.sub("", rest[len(particle) :], count=1)
        elif any(p.startswith(rest) for p in NOT_AVAILABLE_PARTICLES):
            return True
    elif NOT_AVAILABLE_APOLOGY.startswith(rest):
        return True
    return any(phrase.startswith(rest) for phrase in NOT_AVAILABLE_PHRASES)


def answer_question(
    question: str,
    history: Sequence[Exchange],
    llm: LLMClient,
    knowledge_base: KnowledgeBase,
    no_answer_text: str,
    *,
    fixed_replies: Mapping[Category, str],
) -> Iterator[AnswerEvent]:
    """Answer one question; see the module docstring for the order of events.

    The filter runs on the question and every history turn before the model is
    called (AD-4); `Meta.personal_info_removed` describes the new question only.
    Then the classify call sorts the cleaned question, given the last
    `CLASSIFY_HISTORY_EXCHANGES` cleaned exchanges (AD-1, AD-5). A category in
    `fixed_replies` gets that text and no answer call (`done` gets the feedback
    question). Any other category is answered like `general` and reported as
    `general`. A classify error, or a category outside the
    closed set, ends in `Failed` before `Meta`: nothing is answered.
    Answer text is held back until the first cited chunk, then released (AD-7).
    With no citation at the end, the held text is dropped and `no_answer_text`
    is sent instead. If the held text could still open with a not-available
    sentence (`NOT_AVAILABLE_OPENING`), it is held on until its first line is
    complete (a line break or the end of the answer); if that line is such a
    sentence without a turn word (`TURN_WORD`), the reply is declined:
    `no_answer_text` is sent at once, the rest of the stream is read only for its
    `Usage` and unknown ids, and `Sources` is empty. The check runs on each chunk
    until it decides; it decides once, before anything is shown, and text already
    sent is never taken back. A cited id that is not
    in the knowledge base is dropped (it does not count as a citation) and counted
    in `Sources.unknown_source_ids`; the answer goes on.
    """
    clean = remove_personal_info(question)
    clean_history = tuple(
        Exchange(
            question=remove_personal_info(exchange.question).text,
            answer=remove_personal_info(exchange.answer).text,
        )
        for exchange in history
    )
    try:
        category, classify_usage = llm.classify(clean.text, clean_history[-CLASSIFY_HISTORY_EXCHANGES:])
    except LLMError as exc:
        yield Failed(reason=type(exc).__name__)
        return
    yield Spent(classify_usage, call="classify")
    if category not in _CATEGORIES:
        # Never the value itself: it came from the model.
        yield Failed(reason=UNKNOWN_CATEGORY_REASON)
        return

    fixed = fixed_replies.get(category)
    if fixed is not None:
        yield Meta(category=category, personal_info_removed=clean.removed, clean_question=clean.text)
        yield TextDelta(fixed)
        yield Sources(())
        yield Done()
        return

    yield Meta(category="general", personal_info_removed=clean.removed, clean_question=clean.text)

    held: list[str] = []
    shown = False  # the reply has started streaming
    declined = False  # the no-answer text was sent instead of the reply
    usage: Usage | None = None
    cited: dict[str, SourceRef] = {}  # insertion order = order of first citation
    unknown: set[str] = set()
    try:
        for item in llm.answer(clean.text, clean_history):
            if isinstance(item, Usage):
                usage = item
                break  # the last item of an answer
            for source_id in item.source_ids:
                if source_id in cited or source_id in unknown:
                    continue
                try:
                    source = knowledge_base.source(source_id)
                except KeyError:
                    unknown.add(source_id)  # no link for it; the rest of the answer is shown
                    continue
                cited[source_id] = SourceRef(source.id, source.title, source.url)
            if declined:
                continue  # read on only for the usage and the unknown ids
            if shown:
                if item.text:
                    yield TextDelta(item.text)
                continue
            held.append(item.text)
            if not cited:
                continue
            decision = _held_reply_declines("".join(held), ended=False)
            if decision is None:
                continue
            if decision:
                declined = True
                yield TextDelta(no_answer_text)
                continue
            shown = True
            text = "".join(held)
            held.clear()
            if text:
                yield TextDelta(text)
    except LLMError as exc:
        yield Failed(reason=type(exc).__name__)
        return

    if not shown and not declined:
        text = "".join(held)
        if not cited or _held_reply_declines(text, ended=True):
            declined = True
            yield TextDelta(no_answer_text)
        elif text:
            yield TextDelta(text)
    # Before `Sources`: a client that leaves at that event still gets its cost logged.
    if usage is not None:
        yield Spent(usage, call="answer")
    yield Sources(() if declined else tuple(cited.values()), unknown_source_ids=len(unknown))
    yield Done()
