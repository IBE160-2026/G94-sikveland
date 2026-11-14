"""A scripted `LLMClient`: answers exactly what the test says, without any network."""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from app.ports.llm import AnswerChunk, Category, Exchange, LLMError, LLMRefusalError, Usage

DEFAULT_USAGE = Usage(input_tokens=100, output_tokens=20, cache_read_tokens=0, cache_write_tokens=0)


@dataclass(frozen=True)
class AnswerCall:
    """One recorded `answer` call."""

    question: str
    history: tuple[Exchange, ...]


class ScriptedLLM:
    """Yields the scripted chunks, then `usage`; or, after the chunks, raises.

    `error` is raised after the chunks (pass no chunks to fail before any text);
    `refusal=True` raises `LLMRefusalError` the same way. Every call is recorded.
    """

    def __init__(
        self,
        chunks: Sequence[AnswerChunk] = (),
        usage: Usage = DEFAULT_USAGE,
        error: LLMError | None = None,
        refusal: bool = False,
    ) -> None:
        self.chunks = tuple(chunks)
        self.usage = usage
        self.error = error
        self.refusal = refusal
        self.calls: list[AnswerCall] = []

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
        raise NotImplementedError("classify comes with the classifier in Epic 2")

    def translate(self, text: str) -> tuple[str, Usage]:
        raise NotImplementedError("translate comes with the English translation in Epic 4")
