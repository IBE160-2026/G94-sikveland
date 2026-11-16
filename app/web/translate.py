"""`POST /api/translate`: the English of one finished reply (FR7, AD-4).

Takes `{text}` and returns `{translation}`. The text is filtered for personal
information first; the Thai of a fixed text or an example question gets its stored
English with no model call and no log line. Anything else goes to `LLMClient.translate`
(the small model with Claude, `OLLAMA_MODEL` with Ollama, `mock_llm` in demo mode), and
one line goes to the request log with the tokens and cost, never the text.

A body sent without `Content-Type: application/json` gets a 415 envelope, an invalid
body the app-wide 422 envelope, and a failed translation a 502 envelope. The text is
never echoed or logged.
"""

import logging
from typing import Annotated, Any

from fastapi import APIRouter, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, StringConstraints, ValidationError

from app.pipeline.cost import Prices
from app.pipeline.translate import StoredEnglish, Translation, translate_reply
from app.ports.llm import LLMClient, Usage
from app.web.request_log import Outcome, RequestLog, request_line

# The longest reply the page keeps (`MAX_ANSWER_CHARS` in `app/web/chat.py`).
MAX_TEXT_CHARS = 10000
JSON_MEDIA_TYPE = "application/json"
WRONG_MEDIA_TYPE_ERROR = {
    "error": {"code": "unsupported_media_type", "message": "Content-Type must be application/json"}
}
FAILED_ERROR = {"error": {"code": "translation_failed", "message": "the text could not be translated"}}

logger = logging.getLogger(__name__)
router = APIRouter()

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=MAX_TEXT_CHARS)]


class TranslateRequest(BaseModel):
    """The request body. Anything else, also an extra field, is rejected with 422."""

    model_config = ConfigDict(extra="forbid")

    text: Text


@router.post("/api/translate", response_model=None)
async def translate(request: Request) -> dict[str, Any] | JSONResponse:
    # Checked before the body is read: FastAPI would not read a `text/plain` body as JSON,
    # and any website can send one from the applicant's browser (a no-cors fetch).
    media_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if media_type != JSON_MEDIA_TYPE:
        return JSONResponse(status_code=415, content=WRONG_MEDIA_TYPE_ERROR)
    try:
        body = TranslateRequest.model_validate_json(await request.body())
    except ValidationError as exc:
        # The app-wide 422 envelope (`app/main.py`); the input is never echoed.
        raise RequestValidationError(exc.errors(include_url=False, include_input=False)) from None
    # The model call blocks, so it runs off the event loop.
    english = await run_in_threadpool(_translate, request, body.text)
    if english is None:
        return JSONResponse(status_code=502, content=FAILED_ERROR)
    return {"translation": english}


def _translate(request: Request, text: str) -> str | None:
    """The English of `text`, or `None` if it failed. A model call writes one log line."""
    state = request.app.state
    llm: LLMClient = state.llm
    stored: StoredEnglish = state.stored_english
    try:
        result: Translation = translate_reply(text, llm, stored)
    except Exception as exc:  # noqa: BLE001 - every failure gets the same envelope
        # By class name only: the message could hold part of the text.
        logger.warning("translation failed: %s", type(exc).__name__)
        _log(state, "error", None)
        return None
    if not result.stored:
        _log(state, "translated", result.usage)
    return result.text


def _log(state: Any, outcome: Outcome, usage: Usage | None) -> None:
    request_log: RequestLog = state.request_log
    # `{"translate": version}`; the model and its prices per mode (set in `app/main.py`).
    prompt_versions: dict[str, str] = state.translate_prompt_versions
    model: str = state.translate_model
    prices: Prices = state.translate_prices
    try:
        request_log.write(
            request_line(
                endpoint="translate",
                outcome=outcome,
                category=None,
                prompt_versions=prompt_versions,
                model=model,
                usage=usage,
                prices=prices,
                classify_usage=None,
                classify_prices=prices,
                unknown_source_ids=None,
            )
        )
    except Exception as exc:  # noqa: BLE001 - the log must never break a translation
        logger.error("request log failed: %s", type(exc).__name__)
