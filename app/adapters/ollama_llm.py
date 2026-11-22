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

The model sometimes writes a Chinese, Japanese or Korean (CJK) word in a Thai answer.
Fullwidth ASCII (digits, brackets, commas) and common CJK punctuation are first mapped
to ASCII (`normalise_script`; the Chinese full stop becomes a space), so they never
count as CJK words.
From the first remaining CJK character on, the answer is held; when the stream has ended, one
small non-streamed call (`prompts/ollama-script-repair.md`, thinking off, reply held to
`REPAIR_SCHEMA`) gives a Thai word for each CJK word, which code puts in its place
(`apply_replacements`); a word without a usable Thai word, or every word when the call
fails, is removed. The held text is then released as one chunk with every held source id.

No `httpx` type or exception leaves this module: failures are `LLMError`. A non-200
status or an `error` line is logged as a warning (status or a fixed reason, never the
response text), so "model not pulled" can be told from "Ollama down".
"""

import difflib
import json
import logging
import re
from collections.abc import Iterator, Mapping, Sequence
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

# Chinese, Japanese and Korean characters: Hangul Jamo, CJK and Kangxi radicals, CJK
# punctuation, kana, Bopomofo, Hangul compatibility Jamo, Kanbun, Bopomofo extension and
# strokes, Katakana extensions, enclosed CJK and CJK compatibility, Han extension A, Han,
# Hangul Jamo extension A, Hangul syllables and Jamo extension B, Han compatibility,
# vertical and CJK compatibility forms, fullwidth and halfwidth forms, kana supplement
# and extensions, and supplementary Han (extensions B to H and compatibility supplement).
# Fullwidth ASCII and the common CJK punctuation are mapped to ASCII first
# (`normalise_script`), so they never count as CJK in an answer.
CJK_CHARS = (
    "\u1100-\u11ff"
    "\u2e80-\u2fdf"
    "\u3000-\u303f"
    "\u3040-\u309f"
    "\u30a0-\u30ff"
    "\u3100-\u312f"
    "\u3130-\u318f"
    "\u3190-\u31ef"
    "\u31f0-\u31ff"
    "\u3200-\u33ff"
    "\u3400-\u4dbf"
    "\u4e00-\u9fff"
    "\ua960-\ua97f"
    "\uac00-\ud7ff"
    "\uf900-\ufaff"
    "\ufe10-\ufe1f"
    "\ufe30-\ufe4f"
    "\uff00-\uffef"
    "\U0001b000-\U0001b16f"
    "\U00020000-\U0003ffff"
)
# Fullwidth ASCII (U+FF01-FF5E) to ASCII, as NFKC does; the ideographic space and the
# Chinese full stop to a space; the ideographic comma to a comma; corner brackets to `"`.
_SCRIPT_NORMALISATION: dict[int, str] = {
    **{code: chr(code - 0xFEE0) for code in range(0xFF01, 0xFF5F)},
    0x3000: " ",
    0x3001: ",",
    0x3002: " ",
    0x300C: '"',
    0x300D: '"',
    0x300E: '"',
    0x300F: '"',
}
CJK = re.compile(f"[{CJK_CHARS}]")
CJK_RUN = re.compile(f"[{CJK_CHARS}]+")
# Characters of answer text on each side of a CJK word, sent with it to the repair call.
REPAIR_CONTEXT_CHARS = 60
MAX_REPLACEMENT_CHARS = 40
REPAIR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "replacements": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"cjk": {"type": "string"}, "thai": {"type": "string"}},
                "required": ["cjk", "thai"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["replacements"],
    "additionalProperties": False,
}
# Fixed reasons for the warning when the repair call gives nothing usable (never model text).
REPAIR_CALL_FAILED = "the repair call failed"
REPAIR_INCOMPLETE = "the repair reply is incomplete"
REPAIR_NOT_JSON = "the repair reply is not JSON"
REPAIR_WRONG_SHAPE = "the repair reply has the wrong shape"
_REPAIR_REASONS = (REPAIR_INCOMPLETE, REPAIR_NOT_JSON, REPAIR_WRONG_SHAPE)


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


def normalise_script(text: str) -> str:
    """`text` with fullwidth ASCII and common CJK punctuation as ASCII, character by character.

    Fullwidth digits, letters and signs become their ASCII forms (as NFKC does), the
    ideographic space and the Chinese full stop a space, the ideographic comma `,`, and
    corner brackets `"`. Per character, so where a stream splits does not matter.
    """
    return text.translate(_SCRIPT_NORMALISATION)


def find_cjk_runs(text: str) -> list[str]:
    """The distinct runs of CJK characters in `text`, in order of first appearance."""
    return list(dict.fromkeys(CJK_RUN.findall(text)))


def repair_user_message(text: str, runs: Sequence[str]) -> str:
    """One numbered entry per run: the run, then the text around its first appearance.

    Up to `REPAIR_CONTEXT_CHARS` characters on each side, `…` where the text was cut,
    and line breaks as spaces, so each entry is two lines.
    """
    first_at: dict[str, int] = {}
    for match in CJK_RUN.finditer(text):
        first_at.setdefault(match.group(0), match.start())
    entries: list[str] = []
    for number, run in enumerate(runs, start=1):
        # A whole run, not the same characters inside a longer run.
        start = first_at.get(run, max(text.find(run), 0))
        end = start + len(run)
        left = max(0, start - REPAIR_CONTEXT_CHARS)
        right = min(len(text), end + REPAIR_CONTEXT_CHARS)
        context = ("…" if left > 0 else "") + text[left:right] + ("…" if right < len(text) else "")
        context = " ".join(context.splitlines())
        entries.append(f"{number}. {run}\n{context}")
    return "\n\n".join(entries)


def build_repair_request(
    *, model: str, num_ctx: int, system: str, text: str, runs: Sequence[str]
) -> dict[str, Any]:
    """The JSON body for the repair `POST /api/chat`: the repair prompt, then the CJK words.

    Same model and `num_ctx` as the answer call, so Ollama does not reload the model.
    No knowledge base, not streamed, thinking off, the reply held to `REPAIR_SCHEMA`.
    """
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": repair_user_message(text, runs)},
        ],
        "stream": False,
        "think": False,
        "format": REPAIR_SCHEMA,
        "options": {"num_ctx": num_ctx},
    }


def usable_replacement(thai: str) -> str | None:
    """The trimmed replacement, or `None` if it may not stand in for a CJK word.

    Usable: non-empty, at most `MAX_REPLACEMENT_CHARS` characters, no CJK character,
    no line break, no `[` or `]` (so it can never form a marker).
    """
    value = thai.strip()
    if not value or len(value) > MAX_REPLACEMENT_CHARS:
        return None
    if CJK.search(value) or "[" in value or "]" in value or value.splitlines() != [value]:
        return None
    return value


def parse_repair_reply(content: str, runs: Sequence[str]) -> dict[str, str]:
    """The usable Thai word for each asked run, from the model's JSON reply.

    A run with no usable word is left out (it will be removed). A reply that is not
    JSON or not of `REPAIR_SCHEMA`'s shape is an `LLMError` with a fixed message.
    """
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise LLMError(REPAIR_NOT_JSON) from exc
    items = data.get("replacements") if isinstance(data, dict) else None
    if not isinstance(items, list):
        raise LLMError(REPAIR_WRONG_SHAPE)
    asked = set(runs)
    replacements: dict[str, str] = {}
    for item in items:
        if not isinstance(item, dict):
            raise LLMError(REPAIR_WRONG_SHAPE)
        cjk, thai = item.get("cjk"), item.get("thai")
        if not isinstance(cjk, str) or not isinstance(thai, str):
            raise LLMError(REPAIR_WRONG_SHAPE)
        if cjk not in asked:
            # Only ASCII whitespace: `str.strip` would also take the ideographic space,
            # which can be part of a run.
            cjk = cjk.strip(" \t\r\n")
        if cjk not in asked or cjk in replacements:
            continue
        value = usable_replacement(thai)
        if value is not None:
            replacements[cjk] = value
    return replacements


def apply_replacements(text: str, replacements: Mapping[str, str]) -> str:
    """`text` with each CJK run replaced by its Thai word, or removed if it has none.

    Only the CJK runs change; every other character stays as it is.
    """
    return CJK_RUN.sub(lambda match: replacements.get(match.group(0), ""), text)


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


class _CjkHold:
    """Holds an answer back from its first CJK character to its end.

    Text before that character passes through; from it on, text and source ids are
    kept (ids once each, in order of first citation) for the repair at the end.
    """

    def __init__(self) -> None:
        self.holding = False
        self.shown_text = ""
        self.held_text = ""
        self.held_ids: list[str] = []

    def pieces(self, content: str) -> list[str]:
        """A streamed piece of answer text, split at its first CJK character.

        The marker parser then releases the markers before that character in a chunk
        of their own, so their ids are not held. Unsplit when there is no CJK
        character, or when the answer is already held.
        """
        first = None if self.holding else CJK.search(content)
        if first is None or first.start() == 0:
            return [content]
        return [content[: first.start()], content[first.start() :]]

    def feed(self, chunk: AnswerChunk) -> AnswerChunk | None:
        """The part of `chunk` that may be shown now, or `None`."""
        if not self.holding:
            first = CJK.search(chunk.text)
            if first is None:
                self.shown_text += chunk.text
                return chunk
            self.holding = True
            before = chunk.text[: first.start()]
            self.shown_text += before
            # Where a chunk's markers stood in its text is not known, so its ids are held
            # with the text from the CJK character on (`pieces` keeps this to rare cases).
            self._hold(chunk.text[first.start() :], chunk.source_ids)
            return _chunk(before, [])
        self._hold(chunk.text, chunk.source_ids)
        return None

    def _hold(self, text: str, source_ids: Sequence[str]) -> None:
        self.held_text += text
        self.held_ids.extend(sid for sid in source_ids if sid not in self.held_ids)


def _added(first: Usage, second: Usage) -> Usage:
    return Usage(
        input_tokens=first.input_tokens + second.input_tokens,
        output_tokens=first.output_tokens + second.output_tokens,
        cache_read_tokens=first.cache_read_tokens + second.cache_read_tokens,
        cache_write_tokens=first.cache_write_tokens + second.cache_write_tokens,
    )


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
        repair_prompt: Prompt,
        client: httpx.Client | None = None,
    ) -> None:
        self._settings = settings
        self._knowledge_base = knowledge_base
        self._prompt = prompt
        self._citing_prompt = citing_prompt
        self._classifier_prompt = classifier_prompt
        self._translate_prompt = translate_prompt
        self._repair_prompt = repair_prompt
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
        hold = _CjkHold()
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
                        for piece in hold.pieces(normalise_script(content)):
                            chunk = parser.feed(piece)
                            if chunk is not None:
                                shown = hold.feed(_resolved(chunk, known_ids))
                                if shown is not None:
                                    yield shown
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
            shown = hold.feed(_resolved(chunk, known_ids))
            if shown is not None:
                yield shown
        usage = Usage(
            input_tokens=_count(final.get("prompt_eval_count")),
            output_tokens=_count(final.get("eval_count")),
            cache_read_tokens=0,
            cache_write_tokens=0,
        )
        if hold.holding:
            # Only now, after the answer stream is done: never alongside it.
            held_text, repair_usage = self._repair(hold.shown_text, hold.held_text)
            released = _chunk(held_text, hold.held_ids)
            if released is not None:
                yield released
            if repair_usage is not None:
                usage = _added(usage, repair_usage)
        yield usage

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

    def _repair(self, shown_text: str, held_text: str) -> tuple[str, Usage | None]:
        """`held_text` with its CJK words replaced by Thai or removed, and the call's tokens.

        Never raises: when the call fails or its reply is unusable, every CJK word is
        removed and a warning with a fixed reason is logged. The tokens are `None` only
        when no reply arrived.
        """
        runs = find_cjk_runs(held_text)
        if not runs:
            return held_text, None
        request = build_repair_request(
            model=self._settings.ollama_model,
            num_ctx=self._settings.ollama_num_ctx,
            system=self._repair_prompt.text,
            text=shown_text + held_text,
            runs=runs,
        )
        replacements: dict[str, str] = {}
        usage: Usage | None = None
        try:
            data = self._post(request, "repair")
            usage = _reply_usage(data)
            if data.get("done") is not True or data.get("done_reason") != "stop":
                raise LLMError(REPAIR_INCOMPLETE)
            content = _reply_text(data)
            if content is None:
                raise LLMError(REPAIR_WRONG_SHAPE)
            replacements = parse_repair_reply(content, runs)
        except Exception as exc:  # noqa: BLE001 -- the answer must never fail because of the repair
            if isinstance(exc, LLMError) and str(exc) in _REPAIR_REASONS:
                reason = str(exc)
            else:
                # The class name only: the message may hold model text.
                reason = f"{REPAIR_CALL_FAILED}: {type(exc).__name__}"
            logger.warning("Script repair gave no Thai words (%s); the CJK words are removed", reason)
        replaced = sum(1 for run in runs if run in replacements)
        logger.info("Script repair: %d replaced, %d removed", replaced, len(runs) - replaced)
        return apply_replacements(held_text, replacements), usage

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
