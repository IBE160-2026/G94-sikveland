"""`POST /api/chat`: one question in, a JSON Lines stream of events out (AD-8).

The only place the stream events are built. Question and answer text never go
to the log; a failure is logged by class name or a short label only. When the
stream ends (done, error or the client going away), one line goes to the request
log (`app/web/request_log.py`).
"""

import json
import logging
from collections.abc import Callable, Iterator
from typing import Annotated, Any

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from app.config import Settings
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
from app.ports.content import ContentStore
from app.ports.knowledge_base import KnowledgeBase
from app.ports.llm import Category, Exchange, LLMClient, Usage
from app.web.request_log import Outcome, RequestLog, answer_prices, request_line

MAX_QUESTION_CHARS = 1000
MAX_ANSWER_CHARS = 10000
MAX_HISTORY_ITEMS = 10
MEDIA_TYPE = "application/jsonl"
ERROR_EVENT: dict[str, Any] = {"type": "error", "key": "error"}

logger = logging.getLogger(__name__)
router = APIRouter()


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
    events = answer_question(
        body.question,
        history,
        llm,
        knowledge_base,
        no_answer_text=content.texts()["reply-no-answer"].th,
    )
    settings: Settings = state.settings
    request_log: RequestLog = state.request_log
    answer_prompt_version: str = state.answer_prompt.version

    def log_request(outcome: Outcome, category: Category | None, usage: Usage | None) -> None:
        request_log.write(
            request_line(
                outcome=outcome,
                category=category,
                answer_prompt_version=answer_prompt_version,
                model=settings.model_answer,
                usage=usage,
                prices=answer_prices(settings),
            )
        )

    return StreamingResponse(
        _lines(events, log_request),
        media_type=MEDIA_TYPE,
        headers={"Cache-Control": "no-store", "X-Accel-Buffering": "no"},
    )


LogRequest = Callable[[Outcome, Category | None, Usage | None], None]


def _lines(events: Iterator[AnswerEvent], log_request: LogRequest) -> Iterator[str]:
    """One JSON object per line; any failure becomes an `error` event that ends the stream.

    `log_request` is called once when the stream ends, also when the server closes
    it because the client went away (outcome `incomplete`). `Spent` is never sent.
    """
    outcome: Outcome = "incomplete"
    category: Category | None = None
    usage: Usage | None = None
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
                    usage = event.usage
                    continue
                case Meta():
                    category = event.category
                case Sources():
                    answered = "answered" if event.items else "no_answer"
                case Done():
                    outcome = answered
            yield _line(_event(event))
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
            log_request(outcome, category, usage)
        except Exception as exc:  # noqa: BLE001 - the log must never break an answer
            logger.error("request log failed: %s", type(exc).__name__)


def _event(event: AnswerEvent) -> dict[str, Any]:
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
            return {
                "type": "sources",
                "sources": [
                    {"id": ref.id, "title": ref.title, "url": ref.url} for ref in event.items
                ],
                # Checklists come in Epic 3.
                "checklist": False,
                "checklist_purposes": [],
            }
        case Done():
            return {"type": "done"}
    raise TypeError(f"unknown answer event {type(event).__name__}")


def _line(event: dict[str, Any]) -> str:
    return json.dumps(event, ensure_ascii=False) + "\n"
