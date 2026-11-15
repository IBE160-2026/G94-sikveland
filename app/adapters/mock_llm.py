"""`LLMClient` for demo mode (`MOCK_LLM=true`): stored answers, no API key (AD-2, AD-15).

Answers the example questions from `content/demo-answers.yaml` through the same
pipeline and stream as a real answer, sources included. Any other question gets
no text at all, so the pipeline sends the fixed `reply-demo-only` text. Every
call reports `Usage(0, 0, 0, 0)`. No SDK, no network.
"""

import re
import time
import unicodedata
from collections.abc import Iterator, Mapping, Sequence

from app.adapters.file_demo_answers import DemoAnswer, DemoAnswers
from app.ports.content import ExampleQuestion, FixedText
from app.ports.llm import AnswerChunk, Category, Exchange, Usage

MODEL_NAME = "mock_llm"
NO_USAGE = Usage(input_tokens=0, output_tokens=0, cache_read_tokens=0, cache_write_tokens=0)
DEMO_ONLY_KEY = "reply-demo-only"
# Words per streamed chunk; Thai separates phrases with spaces, so a chunk never splits a word.
WORDS_PER_CHUNK = 3
_WORD = re.compile(r"\S+\s*")


# Emoji parts that are not symbols by Unicode category: variation selectors (U+FE0E,
# U+FE0F), the zero-width joiner and the keycap mark.
_EMOJI_MARKS = frozenset("\ufe0e\ufe0f\u200d\u20e3")


def normalise(text: str) -> str:
    """NFC form, trimmed, every run of whitespace collapsed to one space, case folded."""
    return " ".join(unicodedata.normalize("NFC", text).split()).casefold()


def done_key(text: str) -> str:
    """`normalise(text)` without the punctuation, symbols and emoji around it.

    `Thanks!`, `ok.` and `ขอบคุณค่ะ 🙏` match the done phrases `thanks`, `ok` and
    `ขอบคุณค่ะ`. Only the ends are trimmed: `thanks, and the fee?` stays a question.
    Thai letters and marks are never trimmed (e.g. the tone mark that ends `ได้`).
    """
    chars = normalise(text)
    start, end = 0, len(chars)
    while start < end and _surrounding(chars[start]):
        start += 1
    while end > start and _surrounding(chars[end - 1]):
        end -= 1
    return chars[start:end]


def _surrounding(char: str) -> bool:
    """Whitespace, punctuation (P*), a symbol or emoji (S*), a format character or an emoji mark."""
    category = unicodedata.category(char)
    return char.isspace() or category[0] in "PS" or category == "Cf" or char in _EMOJI_MARKS


class MockLLM:
    """Stored demo answers keyed by the normalised Thai and English example questions.

    `pause_seconds` is waited before each chunk after the first, so the page shows
    the answer arriving bit by bit; tests pass 0.
    """

    def __init__(
        self,
        demo: DemoAnswers,
        example_questions: Sequence[ExampleQuestion],
        texts: Mapping[str, FixedText],
        pause_seconds: float = 0.0,
    ) -> None:
        self._pause_seconds = pause_seconds
        self._by_question: dict[str, DemoAnswer] = {}
        for question in example_questions:
            answer = demo.answers[question.id]
            for text in (question.th, question.en):
                self._by_question[normalise(text)] = answer
        self._done_phrases = frozenset(done_key(p) for p in demo.done_phrases) - {""}

        # translate: every stored Thai text this mode can show, to its stored English.
        self._english: dict[str, str] = {}
        for text in texts.values():
            self._english[normalise(text.th)] = text.en
        for question in example_questions:
            self._english[normalise(question.th)] = question.en
        for answer in demo.answers.values():
            self._english[normalise(answer.th)] = answer.en
        self._fallback_english = texts[DEMO_ONLY_KEY].en

    def answer(self, question: str, history: Sequence[Exchange]) -> Iterator[AnswerChunk | Usage]:
        """The stored answer in several chunks, all sources on the first; else no text."""
        stored = self._by_question.get(normalise(question))
        return self._stream(stored)

    def _stream(self, stored: DemoAnswer | None) -> Iterator[AnswerChunk | Usage]:
        if stored is not None:
            for index, text in enumerate(_chunks(stored.th)):
                if index and self._pause_seconds > 0:
                    time.sleep(self._pause_seconds)
                yield AnswerChunk(text, stored.source_ids if index == 0 else ())
        yield NO_USAGE

    def classify(self, question: str, recent_history: Sequence[Exchange]) -> tuple[Category, Usage]:
        """`done` for a done phrase, the stored category for an example question, else `general`.

        A done phrase matches with punctuation and emoji around it (`done_key`).
        """
        if done_key(question) in self._done_phrases:
            return "done", NO_USAGE
        stored = self._by_question.get(normalise(question))
        return (stored.category if stored is not None else "general"), NO_USAGE

    def translate(self, text: str) -> tuple[str, Usage]:
        """The stored English of a stored Thai text; anything else gets `reply-demo-only` in English."""
        return self._english.get(normalise(text), self._fallback_english), NO_USAGE


def _chunks(text: str) -> list[str]:
    """`text` cut into pieces of a few words each; joined they give `text` back exactly."""
    words = _WORD.findall(text)
    leading = text[: len(text) - len("".join(words))]
    pieces = ["".join(words[i : i + WORDS_PER_CHUNK]) for i in range(0, len(words), WORDS_PER_CHUNK)]
    if not pieces:
        return [text] if text else []
    pieces[0] = leading + pieces[0]
    return pieces
