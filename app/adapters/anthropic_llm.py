"""`LLMClient` on the Anthropic API: the only module that imports `anthropic` (AD-2).

No SDK type or SDK exception leaves this module: answers come out as `AnswerChunk`s
and `Usage`, failures as `LLMError`.
"""

from collections.abc import Iterator, Sequence
from typing import Any

import anthropic

from app.adapters.classifier_request import CATEGORY_SCHEMA, classifier_user_message, parse_category
from app.adapters.file_prompts import Prompt
from app.config import Settings
from app.ports.knowledge_base import KnowledgeBase, Source
from app.ports.llm import (
    AnswerChunk,
    Category,
    Exchange,
    LLMError,
    LLMRefusalError,
    Usage,
)

MAX_TOKENS_ANSWER = 32000
# The reply is one short JSON object; the rest is room for the model's own thinking.
MAX_TOKENS_CLASSIFY = 4096
# Stop reasons that mean the answer is complete.
_COMPLETE = frozenset({"end_turn", "stop_sequence"})


def build_answer_request(
    *,
    model: str,
    effort: str,
    system: str,
    documents: Sequence[Source],
    question: str,
    history: Sequence[Exchange],
) -> dict[str, Any]:
    """Keyword arguments for `messages.stream` (AD-7).

    The order never changes, so the prompt cache hits: system prompt, then every
    document (in the given order, Citations on, one cache breakpoint on the last),
    then the history as plain-text turns, then the question.
    """
    if not documents:
        raise LLMError("the answer request needs at least one knowledge-base document")
    blocks: list[dict[str, Any]] = [
        {
            "type": "document",
            "source": {"type": "text", "media_type": "text/plain", "data": source.text},
            "title": source.title,
            "citations": {"enabled": True},
        }
        for source in documents
    ]
    blocks[-1]["cache_control"] = {"type": "ephemeral"}

    questions = [exchange.question for exchange in history] + [question]
    answers = [exchange.answer for exchange in history]
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": [*blocks, {"type": "text", "text": questions[0]}]}
    ]
    for answer, next_question in zip(answers, questions[1:], strict=True):
        messages.append({"role": "assistant", "content": answer})
        messages.append({"role": "user", "content": next_question})

    return {
        "model": model,
        "max_tokens": MAX_TOKENS_ANSWER,
        "system": system,
        "messages": messages,
        "thinking": {"type": "adaptive"},
        "output_config": {"effort": effort},
    }


def build_classify_request(
    *,
    model: str,
    effort: str,
    system: str,
    question: str,
    recent_history: Sequence[Exchange],
) -> dict[str, Any]:
    """Keyword arguments for `messages.create` (AD-5, AD-14).

    Structured output (`output_config.format`) holds the reply to the category
    schema; there are no tools, so no forced tool use. `thinking` is not sent:
    the small model decides, and `effort` keeps it short.
    """
    return {
        "model": model,
        "max_tokens": MAX_TOKENS_CLASSIFY,
        "system": system,
        "messages": [{"role": "user", "content": classifier_user_message(question, recent_history)}],
        "output_config": {
            "effort": effort,
            "format": {"type": "json_schema", "schema": CATEGORY_SCHEMA},
        },
    }


class AnthropicLLM:
    """The real model. Building it needs no network: the SDK client connects on first call."""

    def __init__(
        self,
        settings: Settings,
        knowledge_base: KnowledgeBase,
        prompt: Prompt,
        classifier_prompt: Prompt,
        client: Any = None,
    ) -> None:
        self._settings = settings
        self._knowledge_base = knowledge_base
        self._prompt = prompt
        self._classifier_prompt = classifier_prompt
        key = settings.anthropic_api_key
        if client is None and key is not None:
            client = anthropic.Anthropic(api_key=key.get_secret_value())
        self._client = client

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        # Sorted here too, so the request order (and the cache) never depends on the store.
        documents = tuple(sorted(self._knowledge_base.documents(), key=lambda s: s.id))
        request = build_answer_request(
            model=self._settings.model_answer,
            effort=self._settings.effort_answer,
            system=self._prompt.text,
            documents=documents,
            question=question,
            history=history,
        )
        try:
            with self._sdk_client().messages.stream(**request) as stream:
                for event in stream:
                    chunk = _chunk(event, documents)
                    if chunk is not None:
                        yield chunk
                message = stream.get_final_message()
        except LLMError:
            raise
        except Exception as exc:
            # SDK errors, and transport errors the SDK lets through mid-stream.
            raise LLMError(f"answer call failed: {type(exc).__name__}") from exc

        if message.stop_reason == "refusal":
            raise LLMRefusalError("the model refused to answer")
        if message.stop_reason not in _COMPLETE:
            raise LLMError(f"the answer is incomplete (stop_reason: {message.stop_reason})")
        yield _usage(message.usage)

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        request = build_classify_request(
            model=self._settings.model_small,
            effort=self._settings.effort_small,
            system=self._classifier_prompt.text,
            question=question,
            recent_history=recent_history,
        )
        try:
            message = self._sdk_client().messages.create(**request)
        except LLMError:
            raise
        except Exception as exc:
            raise LLMError(f"classify call failed: {type(exc).__name__}") from exc

        if message.stop_reason == "refusal":
            raise LLMRefusalError("the model refused to classify")
        if message.stop_reason not in _COMPLETE:
            raise LLMError(f"the classification is incomplete (stop_reason: {message.stop_reason})")
        text = "".join(block.text for block in message.content if block.type == "text")
        return parse_category(text), _usage(message.usage)

    def translate(self, text: str) -> tuple[str, Usage]:
        raise NotImplementedError("translate comes with the English translation in Epic 4")

    def _sdk_client(self) -> Any:
        if self._client is None:
            raise LLMError("ANTHROPIC_API_KEY is not set")
        return self._client


def _chunk(event: Any, documents: Sequence[Source]) -> AnswerChunk | None:
    """The chunk for one stream event, or `None` for events that carry no answer."""
    if event.type != "content_block_delta":
        return None
    delta = event.delta
    if delta.type == "text_delta":
        return AnswerChunk(delta.text, ())
    if delta.type == "citations_delta":
        index = getattr(delta.citation, "document_index", None)
        if not isinstance(index, int) or not 0 <= index < len(documents):
            raise LLMError(f"citation refers to unknown document index {index!r}")
        return AnswerChunk("", (documents[index].id,))
    return None  # thinking and signature deltas


def _usage(usage: Any) -> Usage:
    return Usage(
        input_tokens=usage.input_tokens,
        output_tokens=usage.output_tokens,
        cache_read_tokens=usage.cache_read_input_tokens or 0,
        cache_write_tokens=usage.cache_creation_input_tokens or 0,
    )
