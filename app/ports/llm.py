"""The language model: the port the pipeline uses for every model call (AD-14).

Adapters (`app/adapters/anthropic_llm.py`, later the demo `mock_llm`) and the test
fake (`tests/fakes/`) implement it exactly. Nothing here depends on an SDK.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import Literal, Protocol

# Closed set of classifier categories (AD-5). Adding one means changing AD-5.
Category = Literal["general", "individual_assessment", "out_of_scope", "reach_person", "done"]


@dataclass(frozen=True)
class Exchange:
    """One earlier question and the answer the applicant saw, as plain text."""

    question: str
    answer: str


@dataclass(frozen=True)
class AnswerChunk:
    """A piece of a streamed answer: new text, and the ids of sources cited at this point."""

    text: str
    source_ids: tuple[str, ...] = ()


@dataclass(frozen=True)
class Usage:
    """Tokens one model call used. `output_tokens` includes thinking."""

    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int


class LLMError(Exception):
    """The model call failed or ended without a complete answer."""


class LLMRefusalError(LLMError):
    """The model refused to answer (`stop_reason: "refusal"`)."""


class LLMClient(Protocol):
    """The three model calls the pipeline makes. Errors are raised as `LLMError`."""

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        """Stream a grounded answer: `AnswerChunk`s, then exactly one `Usage` last."""
        ...

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        """The category of the question, given the last exchanges."""
        ...

    def translate(self, text: str) -> tuple[str, Usage]:
        """The text translated to English."""
        ...
