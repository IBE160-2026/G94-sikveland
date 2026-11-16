"""A scripted `LLMClient`: answers exactly what the test says, without any network."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from app.ports.llm import AnswerChunk, Category, Exchange, LLMError, LLMRefusalError, Usage

DEFAULT_USAGE = Usage(input_tokens=100, output_tokens=20, cache_read_tokens=0, cache_write_tokens=0)
CLASSIFY_USAGE = Usage(input_tokens=400, output_tokens=20, cache_read_tokens=0, cache_write_tokens=0)
TRANSLATE_USAGE = Usage(input_tokens=600, output_tokens=150, cache_read_tokens=0, cache_write_tokens=0)
DEFAULT_TRANSLATION = "The scripted English."


@dataclass(frozen=True)
class AnswerCall:
    """One recorded `answer` call."""

    question: str
    history: tuple[Exchange, ...]


@dataclass(frozen=True)
class ClassifyCall:
    """One recorded `classify` call."""

    question: str
    recent_history: tuple[Exchange, ...]


class ScriptedLLM:
    """Yields the scripted chunks, then `usage`; or, after the chunks, raises.

    `error` is raised after the chunks (pass no chunks to fail before any text);
    `refusal=True` raises `LLMRefusalError` the same way. `classify` returns
    `category` (any string, so a test can send one outside the closed set) and
    `classify_usage`, or raises `classify_error`. `translate` returns `translation`
    and `translate_usage`, or raises `translate_error` (any exception, so a test can
    send `NotImplementedError`). Every call is recorded: answer calls in `calls`,
    classify calls in `classify_calls`, the texts sent to translate in `translate_calls`.
    """

    def __init__(
        self,
        chunks: Sequence[AnswerChunk] = (),
        usage: Usage = DEFAULT_USAGE,
        error: LLMError | None = None,
        refusal: bool = False,
        category: str = "general",
        classify_usage: Usage = CLASSIFY_USAGE,
        classify_error: LLMError | None = None,
        translation: str = DEFAULT_TRANSLATION,
        translate_usage: Usage = TRANSLATE_USAGE,
        translate_error: Exception | None = None,
    ) -> None:
        self.chunks = tuple(chunks)
        self.usage = usage
        self.error = error
        self.refusal = refusal
        self.category = category
        self.classify_usage = classify_usage
        self.classify_error = classify_error
        self.translation = translation
        self.translate_usage = translate_usage
        self.translate_error = translate_error
        self.calls: list[AnswerCall] = []
        self.classify_calls: list[ClassifyCall] = []
        self.translate_calls: list[str] = []

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        # Recorded at call time, not when the caller starts reading the stream.
        self.calls.append(AnswerCall(question, tuple(history)))
        return self._stream()

    def _stream(self) -> Iterator[AnswerChunk | Usage]:
        yield from self.chunks
        if self.refusal:
            raise LLMRefusalError("scripted refusal")
        if self.error is not None:
            raise self.error
        yield self.usage

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        self.classify_calls.append(ClassifyCall(question, tuple(recent_history)))
        if self.classify_error is not None:
            raise self.classify_error
        return self.category, self.classify_usage  # type: ignore[return-value]

    def translate(self, text: str) -> tuple[str, Usage]:
        self.translate_calls.append(text)
        if self.translate_error is not None:
            raise self.translate_error
        return self.translation, self.translate_usage
