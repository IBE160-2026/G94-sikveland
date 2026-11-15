"""`LLMClient` on a local Ollama server (`/api/chat`), the alternative to Claude.

Ollama has no Citations, so the model marks its sources in the text as `[[source-id]]`
(`prompts/answer-citing-markers.md`). The marker parser here turns markers into
`AnswerChunk.source_ids` and strips them, and the spaces and tabs before them, from
the text (line breaks stay, so list items never merge); a split marker is never shown.
Thinking is on, but its text is never passed on. Classifying is a short
non-streaming call with thinking off and the reply held to the category schema
(`format`).

No `httpx` type or exception leaves this module: failures are `LLMError`. A non-200
status or an `error` line is logged as a warning (status or a fixed reason, never the
response text), so "model not pulled" can be told from "Ollama down".
"""

import json
import logging
import re
from collections.abc import Iterator, Sequence
from html import escape
from typing import Any

import httpx

from app.adapters.classifier_request import CATEGORY_SCHEMA, classifier_user_message, parse_category
from app.adapters.file_prompts import Prompt
from app.config import Settings
from app.ports.knowledge_base import KnowledgeBase, Source
from app.ports.llm import AnswerChunk, Category, Exchange, LLMError, Usage

# Connecting to a local server is quick; the first answer waits for the whole
# knowledge base to be read, which on a laptop can take minutes.
TIMEOUT = httpx.Timeout(connect=5.0, read=300.0, write=30.0, pool=5.0)
MAX_MARKER_BODY = 80
OLLAMA_ERROR_REASON = "Ollama reported an error"

logger = logging.getLogger(__name__)

# A character of a marker body: anything but a bracket or a line break.
_BODY_CHAR = r"[^\[\]\n]"
# A complete marker, with the spaces and tabs before it (stripped together with it).
_MARKER = re.compile(rf"[ \t]*\[\[({_BODY_CHAR}{{1,{MAX_MARKER_BODY}}})\]\]")
# A tail that could still become a marker: spaces/tabs, `[`, `[[`, `[[partial-id`, `[[id]`.
_OPEN_TAIL = re.compile(rf"[ \t]*(?:\[\[?|\[\[{_BODY_CHAR}{{0,{MAX_MARKER_BODY}}}\]?)?\Z")


def build_system_prompt(prompt: Prompt, citing_prompt: Prompt, documents: Sequence[Source]) -> str:
    """The system message: answer prompt, citing prompt, then one block per document.

    Holds no per-request data, so it is byte-identical between requests and Ollama
    can reuse its cached prompt.
    """
    blocks = [
        f'<document id="{escape(source.id)}" title="{escape(source.title)}">\n{source.text}\n</document>'
        for source in documents
    ]
    return "\n\n".join([prompt.text, citing_prompt.text, *blocks])


def build_chat_request(
    *,
    model: str,
    num_ctx: int,
    system: str,
    question: str,
    history: Sequence[Exchange],
) -> dict[str, Any]:
    """The JSON body for `POST /api/chat`: system, the history as plain turns, the question."""
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for exchange in history:
        messages.append({"role": "user", "content": exchange.question})
        messages.append({"role": "assistant", "content": exchange.answer})
    messages.append({"role": "user", "content": question})
    return {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": True,
        "options": {"num_ctx": num_ctx},
    }


def build_classify_request(
    *,
    model: str,
    num_ctx: int,
    system: str,
    question: str,
    recent_history: Sequence[Exchange],
) -> dict[str, Any]:
    """The JSON body for the classify `POST /api/chat`: the classifier prompt, then the question.

    Same model and `num_ctx` as the answer call, so Ollama does not reload the model
    between the two calls. Not streamed, thinking off, the reply held to the schema.
    """
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": classifier_user_message(question, recent_history)},
        ],
        "stream": False,
        "think": False,
        "format": CATEGORY_SCHEMA,
        "options": {"num_ctx": num_ctx},
    }


class MarkerParser:
    """Turns streamed text with `[[id]]` markers into `AnswerChunk`s without the markers.

    A tail that could still become a marker is held back until the next piece (or
    `finish`), so no part of a marker is ever shown. A marker body is 1-80 characters
    without brackets or line breaks; anything else is shown as written.
    """

    def __init__(self) -> None:
        self._pending = ""

    def feed(self, text: str) -> AnswerChunk | None:
        """The chunk for this piece of text, or `None` if nothing can be released yet."""
        buffer = self._pending + text
        parts: list[str] = []
        ids: list[str] = []
        position = 0
        for match in _MARKER.finditer(buffer):
            source_id = match.group(1).strip()
            if not source_id:
                continue  # `[[ ]]`: not a marker, stays in the text
            parts.append(buffer[position : match.start()])
            ids.append(source_id)
            position = match.end()
        rest = buffer[position:]
        hold = _OPEN_TAIL.search(rest)
        cut = hold.start() if hold is not None else len(rest)
        parts.append(rest[:cut])
        self._pending = rest[cut:]
        return _chunk("".join(parts), ids)

    def finish(self) -> AnswerChunk | None:
        """Release what was held back: at the end of the answer it can no longer be a marker."""
        rest, self._pending = self._pending, ""
        return _chunk(rest, [])


def _chunk(text: str, ids: list[str]) -> AnswerChunk | None:
    return AnswerChunk(text, tuple(ids)) if text or ids else None


class OllamaLLM:
    """A model served by Ollama. Building it needs no network: the client connects on first call."""

    def __init__(
        self,
        settings: Settings,
        knowledge_base: KnowledgeBase,
        prompt: Prompt,
        citing_prompt: Prompt,
        classifier_prompt: Prompt,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._knowledge_base = knowledge_base
        self._prompt = prompt
        self._citing_prompt = citing_prompt
        self._classifier_prompt = classifier_prompt
        self._client = client if client is not None else httpx.Client(timeout=TIMEOUT)
        self._url = settings.ollama_base_url.rstrip("/") + "/api/chat"

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        # Sorted here too, so the system message (and Ollama's cache) never depends on the store.
        documents = tuple(sorted(self._knowledge_base.documents(), key=lambda s: s.id))
        if not documents:
            raise LLMError("the answer request needs at least one knowledge-base document")
        request = build_chat_request(
            model=self._settings.ollama_model,
            num_ctx=self._settings.ollama_num_ctx,
            system=build_system_prompt(self._prompt, self._citing_prompt, documents),
            question=question,
            history=history,
        )
        parser = MarkerParser()
        final: dict[str, Any] | None = None
        try:
            with self._client.stream("POST", self._url, json=request) as response:
                if response.status_code != 200:
                    # 404 is usually a model that is not pulled; the body is never logged.
                    logger.warning("Ollama answered HTTP %d", response.status_code)
                    raise LLMError(f"answer call failed: HTTP {response.status_code}")
                for line in response.iter_lines():
                    if not line.strip():
                        continue
                    data = _parse_line(line)
                    message = data.get("message")
                    content = message.get("content") if isinstance(message, dict) else None
                    # `message.thinking` is never read: thinking is not shown, stored or logged.
                    if isinstance(content, str) and content:
                        chunk = parser.feed(content)
                        if chunk is not None:
                            yield chunk
                    if data.get("done") is True:
                        final = data
                        break
        except LLMError:
            raise
        except Exception as exc:
            # Connection refused, timeouts, and transport errors mid-stream.
            raise LLMError(f"answer call failed: {type(exc).__name__}") from exc

        if final is None:
            raise LLMError("the answer is incomplete (the stream ended before done)")
        done_reason = final.get("done_reason")
        if done_reason != "stop":
            raise LLMError(f"the answer is incomplete (done_reason: {done_reason})")
        chunk = parser.finish()
        if chunk is not None:
            yield chunk
        yield Usage(
            input_tokens=_count(final.get("prompt_eval_count")),
            output_tokens=_count(final.get("eval_count")),
            cache_read_tokens=0,
            cache_write_tokens=0,
        )

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        request = build_classify_request(
            model=self._settings.ollama_model,
            num_ctx=self._settings.ollama_num_ctx,
            system=self._classifier_prompt.text,
            question=question,
            recent_history=recent_history,
        )
        try:
            response = self._client.post(self._url, json=request)
            if response.status_code != 200:
                # 404 is usually a model that is not pulled; the body is never logged.
                logger.warning("Ollama answered HTTP %d", response.status_code)
                raise LLMError(f"classify call failed: HTTP {response.status_code}")
            data = _parse_line(response.text)
        except LLMError:
            raise
        except Exception as exc:
            # Connection refused, timeouts and other transport errors.
            raise LLMError(f"classify call failed: {type(exc).__name__}") from exc

        if data.get("done") is not True or data.get("done_reason") != "stop":
            raise LLMError(f"the classification is incomplete (done_reason: {data.get('done_reason')})")
        message = data.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, str):
            raise LLMError("the classifier reply has no text")
        usage = Usage(
            input_tokens=_count(data.get("prompt_eval_count")),
            output_tokens=_count(data.get("eval_count")),
            cache_read_tokens=0,
            cache_write_tokens=0,
        )
        return parse_category(content), usage

    def translate(self, text: str) -> tuple[str, Usage]:
        raise NotImplementedError("translate comes with the English translation in Epic 4")


def _parse_line(line: str) -> dict[str, Any]:
    """One JSON line (of the stream, or the whole classify reply).

    An `error` field or a malformed line is an `LLMError`.
    """
    try:
        data = json.loads(line)
    except ValueError as exc:
        raise LLMError("Ollama sent a line that is not JSON") from exc
    if not isinstance(data, dict):
        raise LLMError("Ollama sent a line that is not a JSON object")
    if "error" in data:
        # The error text is neither logged nor passed on: it may echo the request.
        logger.warning(OLLAMA_ERROR_REASON)
        raise LLMError(OLLAMA_ERROR_REASON)
    return data


def _count(value: Any) -> int:
    """A token count from the final line; missing or malformed counts are 0."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
