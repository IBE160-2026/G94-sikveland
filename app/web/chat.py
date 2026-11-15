"""`POST /api/chat`: one question in, a JSON Lines stream of events out (AD-8).

The only place the stream events are built. The `sources` event also names the visit
purposes whose checklists link a cited source (AD-11), worked out from the fixed
checklists, never by the model. Question and answer text never go to the log; a failure
is logged by class name or a short label only. When the stream ends (done, error or the
client going away), one line goes to the request log (`app/web/request_log.py`).
"""

import json
import logging
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from typing import Annotated, Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.pipeline.answer import (
    AnswerEvent,
    Done,
    Failed,
    Meta,
    Sources,
    Spent,
    TextDelta,
    answer_question,
)
from app.pipeline.cost import Prices
from app.ports.content import VISIT_PURPOSES, ChecklistItem, ContentStore
from app.ports.knowledge_base import KnowledgeBase
from app.ports.llm import Category, Exchange, LLMClient, Usage
from app.web.request_log import Outcome, RequestLog, request_line

MAX_QUESTION_CHARS = 1000
MAX_ANSWER_CHARS = 10000
MAX_HISTORY_ITEMS = 10
MEDIA_TYPE = "application/jsonl"
ERROR_EVENT: dict[str, Any] = {"type": "error", "key": "error"}
# Categories answered with a fixed text instead of an answer call (AD-6). A `done` reply
# is the feedback question; the page shows the Yes/No buttons under it (AD-10).
FIXED_REPLY_KEYS: Mapping[Category, str] = {
    "individual_assessment": "reply-embassy-decides",
    "out_of_scope": "reply-out-of-scope",
    "reach_person": "reply-reach-person",
    "done": "feedback-question",
}

logger = logging.getLogger(__name__)
router = APIRouter()

# Source id -> the visit purposes whose checklist has an item with that source.
ChecklistPurposes = Mapping[str, tuple[str, ...]]
# For a reply that is not a model answer: never a checklist button.
NO_CHECKLISTS: ChecklistPurposes = {}


def checklist_purposes_by_source(checklists: Mapping[str, Sequence[ChecklistItem]]) -> ChecklistPurposes:
    """Each linked source id with its visit purposes, in `VISIT_PURPOSES` order, each once.

    Built once at startup (`app/main.py`) from `ContentStore.checklists()`.
    """
    by_source: dict[str, list[str]] = {}
    for purpose in VISIT_PURPOSES:
        for item in checklists.get(purpose, ()):
            purposes = by_source.setdefault(item.source_id, [])
            if purpose not in purposes:
                purposes.append(purpose)
    return {source_id: tuple(purposes) for source_id, purposes in by_source.items()}


def checklist_purposes(source_ids: Iterable[str], by_source: ChecklistPurposes) -> list[str]:
    """The visit purposes whose checklist links one of `source_ids`, in `VISIT_PURPOSES` order.

    Empty when no id is linked; ids that are not linked (or unknown) count for nothing.
    """
    found = {purpose for source_id in source_ids for purpose in by_source.get(source_id, ())}
    return [purpose for purpose in VISIT_PURPOSES if purpose in found]


Question = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_QUESTION_CHARS),
]
Answer = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_ANSWER_CHARS),
]


class HistoryItem(BaseModel):
    """One earlier exchange, as the page stored it. Empty turns would break the model request."""

    model_config = ConfigDict(extra="forbid")

    question: Question
    answer: Answer


class ChatRequest(BaseModel):
    """The request body. Anything else is rejected with 422 before the model is called."""

    model_config = ConfigDict(extra="forbid")

    question: Question
    history: Annotated[list[HistoryItem], Field(max_length=MAX_HISTORY_ITEMS)] = []


@router.post("/api/chat")
def chat(body: ChatRequest, request: Request) -> StreamingResponse:
    state = request.app.state
    content: ContentStore = state.content
    llm: LLMClient = state.llm
    knowledge_base: KnowledgeBase = state.knowledge_base
    history = [Exchange(question=item.question, answer=item.answer) for item in body.history]
    texts = content.texts()
    events = answer_question(
        body.question,
        history,
        llm,
        knowledge_base,
        # `reply-demo-only` in demo mode, `reply-no-answer` otherwise (set in `app/main.py`).
        no_answer_text=texts[state.no_answer_key].th,
        fixed_replies={category: texts[key].th for category, key in FIXED_REPLY_KEYS.items()},
    )
    request_log: RequestLog = state.request_log
    # `answer` and `classifier`, and with Ollama also `citing` (set in `app/main.py`).
    prompt_versions: dict[str, str] = state.prompt_versions
    # `mock_llm` at no cost in demo mode, the answer model and its prices otherwise.
    model: str = state.answer_model
    prices: Prices = state.answer_prices
    # `PRICE_SMALL_*` with Claude, no cost in demo mode and with Ollama.
    classify_prices: Prices = state.classify_prices
    # Zero usage in demo mode, so every demo line records cost 0.0; `None` otherwise.
    fallback_usage: Usage | None = state.fallback_usage
    # Built from the checklists at startup (`app/main.py`), the same for every provider.
    by_source: ChecklistPurposes = state.checklist_purposes

    def log_request(
        outcome: Outcome,
        category: Category | None,
        usage: Usage | None,
        classify_usage: Usage | None,
        unknown_source_ids: int | None,
    ) -> None:
        # The fallback stands in only for calls that were made: classify always runs
        # first, the answer call only for `general`.
        if usage is None and category == "general":
            usage = fallback_usage
        request_log.write(
            request_line(
                outcome=outcome,
                category=category,
                prompt_versions=prompt_versions,
                model=model,
                usage=usage,
                prices=prices,
                classify_usage=classify_usage if classify_usage is not None else fallback_usage,
                classify_prices=classify_prices,
                unknown_source_ids=unknown_source_ids,
            )
        )

    return StreamingResponse(
        _lines(events, log_request, by_source),
        media_type=MEDIA_TYPE,
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


LogRequest = Callable[[Outcome, Category | None, Usage | None, Usage | None, int | None], None]


def _lines(
    events: Iterator[AnswerEvent], log_request: LogRequest, by_source: ChecklistPurposes
) -> Iterator[str]:
    """One JSON object per line; any failure becomes an `error` event that ends the stream.

    `log_request` is called once when the stream ends, also when the server closes
    it because the client went away (outcome `incomplete`). `Spent` is never sent,
    and the count of dropped unknown source ids goes to the log only. A reply to any
    category but `general` is a fixed reply (outcome `fixed_reply`) and never links a
    checklist; `by_source` gives the checklist purposes of a `general` answer's sources.
    """
    outcome: Outcome = "incomplete"
    category: Category | None = None
    usage: Usage | None = None
    classify_usage: Usage | None = None
    unknown_source_ids: int | None = None
    answered: Outcome = "no_answer"
    try:
        for event in events:
            match event:
                case Failed():
                    outcome = "error"
                    logger.warning("chat answer failed: %s", event.reason)
                    yield _line(ERROR_EVENT)
                    return
                case Spent():
                    if event.call == "classify":
                        classify_usage = event.usage
                    else:
                        usage = event.usage
                    continue
                case Meta():
                    category = event.category
                case Sources():
                    if category != "general":
                        answered = "fixed_reply"
                    else:
                        answered = "answered" if event.items else "no_answer"
                    unknown_source_ids = event.unknown_source_ids
                case Done():
                    outcome = answered
            yield _line(_event(event, by_source if category == "general" else NO_CHECKLISTS))
    except Exception as exc:  # noqa: BLE001 - the stream must end with an event, not a cut
        outcome = "error"
        logger.error("chat stream failed: %s", type(exc).__name__)
        yield _line(ERROR_EVENT)
    finally:
        try:
            # Ends the model stream now rather than at garbage collection.
            close = getattr(events, "close", None)
            if close is not None:
                close()
        except Exception as exc:  # noqa: BLE001 - logging below must still run
            logger.error("closing the answer stream failed: %s", type(exc).__name__)
        try:
            log_request(outcome, category, usage, classify_usage, unknown_source_ids)
        except Exception as exc:  # noqa: BLE001 - the log must never break an answer
            logger.error("request log failed: %s", type(exc).__name__)


def _event(event: AnswerEvent, by_source: ChecklistPurposes) -> dict[str, Any]:
    match event:
        case Meta():
            return {
                "type": "meta",
                "category": event.category,
                "personal_info_removed": event.personal_info_removed,
                "clean_question": event.clean_question,
            }
        case TextDelta():
            return {"type": "text", "delta": event.text}
        case Sources():
            # Only cited known sources count (unknown ids were dropped by the pipeline). A
            # fixed reply and the no-answer reply have no sources, so no checklist either.
            purposes = checklist_purposes((ref.id for ref in event.items), by_source)
            return {
                "type": "sources",
                "sources": [{"id": ref.id, "title": ref.title, "url": ref.url} for ref in event.items],
                "checklist": bool(purposes),
                "checklist_purposes": purposes,
            }
        case Done():
            return {"type": "done"}
    raise TypeError(f"unknown answer event {type(event).__name__}")


def _line(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"
