"""`LLMClient` on a local Ollama server (`/api/chat`), the alternative to Claude.

Ollama has no Citations, so the model marks its sources in the text as `[[source-id]]`
(`prompts/answer-citing-markers.md`). The marker parser here turns markers into
`AnswerChunk.source_ids` and strips them, and the spaces and tabs before them, from
the text (line breaks stay, so list items never merge); a split marker is never shown.
A marker id that is not a known document id is mapped to the closest known id when it
is a near-miss spelling of one (`resolve_source_id`); any other id is passed on, and
the pipeline drops it (AD-7).
Thinking follows `OLLAMA_THINK` (on by default), and its text is never passed on. Classifying is a short
non-streaming call with thinking off and the reply held to the category schema
(`format`). Translating is a non-streaming call with thinking off, too.

No `httpx` type or exception leaves this module: failures are `LLMError`. A non-200
status or an `error` line is logged as a warning (status or a fixed reason, never the
response text), so "model not pulled" can be told from "Ollama down".
"""

import difflib
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
# How similar (difflib ratio) a misspelled marker id must be to a known document id to
# be mapped to it. No two known ids are more than 0.8 similar to each other today.
CLOSEST_ID_CUTOFF = 0.85
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
    think: bool,
    system: str,
    question: str,
    history: Sequence[Exchange],
) -> dict[str, Any]:
    """The JSON body for `POST /api/chat`: system, the history as plain turns, the question.

    `think` is `OLLAMA_THINK`: off for a model without Ollama's thinking capability.
    """
    messages: list[dict[str, str]] = [{"role": "system", "content": system}]
    for exchange in history:
        messages.append({"role": "user", "content": exchange.question})
        messages.append({"role": "assistant", "content": exchange.answer})
    messages.append({"role": "user", "content": question})
    return {
        "model": model,
        "messages": messages,
        "stream": True,
        "think": think,
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


def build_translate_request(*, model: str, num_ctx: int, system: str, text: str) -> dict[str, Any]:
    """The JSON body for the translate `POST /api/chat`: the translate prompt, then the text.

    Same model and `num_ctx` as the other calls, so Ollama does not reload the model.
    Not streamed, thinking off.
    """
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": text},
        ],
        "stream": False,
        "think": False,
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


def normalise_source_id(source_id: str) -> str:
    """A marker id trimmed, in lower case, with spaces and underscores turned into hyphens."""
    return re.sub(r"[\s_]+", "-", source_id.strip().lower())


def closest_known_ids(source_id: str, known_ids: Sequence[str]) -> list[tuple[float, str]]:
    """Every known id with its difflib ratio to the normalised `source_id`, most similar first."""
    normalised = normalise_source_id(source_id)
    return sorted(
        ((difflib.SequenceMatcher(None, normalised, known).ratio(), known) for known in known_ids),
        reverse=True,
    )


def resolve_source_id(source_id: str, known_ids: Sequence[str]) -> str:
    """The known document id a marker id means, or the marker id unchanged.

    An exact id is kept. Otherwise the id is normalised (`normalise_source_id`) and,
    if still unknown, mapped to the most similar known id when the similarity is at
    least `CLOSEST_ID_CUTOFF`; a tie maps nothing.
    """
    if source_id in known_ids:
        return source_id
    normalised = normalise_source_id(source_id)
    if normalised in known_ids:
        return normalised
    scored = closest_known_ids(source_id, known_ids)
    if not scored or scored[0][0] < CLOSEST_ID_CUTOFF:
        return source_id
    if len(scored) > 1 and scored[1][0] == scored[0][0]:
        return source_id
    # Only the known id is logged, never the model's text: mapped ids no longer count
    # as unknown in the request log, so this line shows how often the matching fires.
    logger.info("Mapped a misspelled source id to %s", scored[0][1])
    return scored[0][1]


def _chunk(text: str, ids: list[str]) -> AnswerChunk | None:
    return AnswerChunk(text, tuple(ids)) if text or ids else None


def _resolved(chunk: AnswerChunk, known_ids: Sequence[str]) -> AnswerChunk:
    if not chunk.source_ids:
        return chunk
    return AnswerChunk(chunk.text, tuple(resolve_source_id(sid, known_ids) for sid in chunk.source_ids))


class OllamaLLM:
    """A model served by Ollama. Building it needs no network: the client connects on first call."""

    def __init__(
        self,
        settings: Settings,
        knowledge_base: KnowledgeBase,
        prompt: Prompt,
        citing_prompt: Prompt,
        classifier_prompt: Prompt,
        translate_prompt: Prompt,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._knowledge_base = knowledge_base
        self._prompt = prompt
        self._citing_prompt = citing_prompt
        self._classifier_prompt = classifier_prompt
        self._translate_prompt = translate_prompt
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
            think=self._settings.ollama_think,
            system=build_system_prompt(self._prompt, self._citing_prompt, documents),
            question=question,
            history=history,
        )
        parser = MarkerParser()
        known_ids = tuple(source.id for source in documents)
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
                            yield _resolved(chunk, known_ids)
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
            yield _resolved(chunk, known_ids)
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
        data = self._post(request, "classify")
        if data.get("done") is not True or data.get("done_reason") != "stop":
            raise LLMError(f"the classification is incomplete (done_reason: {data.get('done_reason')})")
        content = _reply_text(data)
        if content is None:
            raise LLMError("the classifier reply has no text")
        return parse_category(content), _reply_usage(data)

    def translate(self, text: str) -> tuple[str, Usage]:
        request = build_translate_request(
            model=self._settings.ollama_model,
            num_ctx=self._settings.ollama_num_ctx,
            system=self._translate_prompt.text,
            text=text,
        )
        data = self._post(request, "translate")
        if data.get("done") is not True or data.get("done_reason") != "stop":
            raise LLMError(f"the translation is incomplete (done_reason: {data.get('done_reason')})")
        content = _reply_text(data)
        translation = content.strip() if content is not None else ""
        if not translation:
            raise LLMError("the translation is empty")
        return translation, _reply_usage(data)

    def _post(self, request: dict[str, Any], call: str) -> dict[str, Any]:
        """One non-streamed `POST /api/chat`: the reply object. Any failure is an `LLMError`."""
        try:
            response = self._client.post(self._url, json=request)
            if response.status_code != 200:
                # 404 is usually a model that is not pulled; the body is never logged.
                logger.warning("Ollama answered HTTP %d", response.status_code)
                raise LLMError(f"{call} call failed: HTTP {response.status_code}")
            return _parse_line(response.text)
        except LLMError:
            raise
        except Exception as exc:
            # Connection refused, timeouts and other transport errors.
            raise LLMError(f"{call} call failed: {type(exc).__name__}") from exc


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


def _reply_text(data: dict[str, Any]) -> str | None:
    """The text of a non-streamed reply, or `None` when it has none."""
    message = data.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return content if isinstance(content, str) else None


def _reply_usage(data: dict[str, Any]) -> Usage:
    """The tokens of a non-streamed reply; Ollama reports no cache use."""
    return Usage(
        input_tokens=_count(data.get("prompt_eval_count")),
        output_tokens=_count(data.get("eval_count")),
        cache_read_tokens=0,
        cache_write_tokens=0,
    )


def _count(value: Any) -> int:
    """A token count from the final line; missing or malformed counts are 0."""
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0
