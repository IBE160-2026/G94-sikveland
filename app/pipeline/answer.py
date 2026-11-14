"""The answer pipeline: filter, then a grounded answer or the no-answer reply (AD-1, AD-7).

Pure logic: the events here are domain values. `app/web` turns them into stream
events (AD-8); nothing here knows about HTTP, JSON or an SDK.

Order of events: one `Meta`, zero or more `TextDelta`, one `Sources`, then `Done`.
`Failed` can come instead of any event after `Meta` and is always the last one.
"""

from collections.abc import Iterator, Sequence
from dataclasses import dataclass

from app.pipeline.filter import remove_personal_info
from app.ports.knowledge_base import KnowledgeBase
from app.ports.llm import Category, Exchange, LLMClient, LLMError, Usage


@dataclass(frozen=True)
class Meta:
    """What the pipeline did with the question before answering it."""

    category: Category
    personal_info_removed: bool
    clean_question: str


@dataclass(frozen=True)
class TextDelta:
    """Answer text to append to what the applicant already sees. Never empty."""

    text: str


@dataclass(frozen=True)
class SourceRef:
    """A cited source, as the applicant sees it."""

    id: str
    title: str
    url: str


@dataclass(frozen=True)
class Sources:
    """Exactly the cited sources, in order of first citation, each once."""

    items: tuple[SourceRef, ...]


@dataclass(frozen=True)
class Done:
    """The answer is complete."""


@dataclass(frozen=True)
class Failed:
    """The answer failed; nothing follows. `reason` is a class name or a short label, never text."""

    reason: str


AnswerEvent = Meta | TextDelta | Sources | Done | Failed


def answer_question(
    question: str,
    history: Sequence[Exchange],
    llm: LLMClient,
    knowledge_base: KnowledgeBase,
    no_answer_text: str,
) -> Iterator[AnswerEvent]:
    """Answer one question; see the module docstring for the order of events.

    The filter runs on the question and every history turn before the model is
    called (AD-4); `Meta.personal_info_removed` describes the new question only.
    Answer text is held back until the first cited chunk, then released (AD-7).
    With no citation at the end, the held text is dropped and `no_answer_text`
    is sent instead. Text already sent is never taken back.
    """
    clean = remove_personal_info(question)
    clean_history = tuple(
        Exchange(
            question=remove_personal_info(exchange.question).text,
            answer=remove_personal_info(exchange.answer).text,
        )
        for exchange in history
    )
    # No classifier yet (Epic 2): every question is a general question.
    yield Meta(category="general", personal_info_removed=clean.removed, clean_question=clean.text)

    held: list[str] = []
    cited: dict[str, SourceRef] = {}  # insertion order = order of first citation
    try:
        for item in llm.answer(clean.text, clean_history):
            if isinstance(item, Usage):
                break  # the last item of an answer; cost logging comes in Story 1.8
            for source_id in item.source_ids:
                if source_id not in cited:
                    try:
                        source = knowledge_base.source(source_id)
                    except KeyError:
                        yield Failed(reason="unknown source id")
                        return
                    cited[source_id] = SourceRef(source.id, source.title, source.url)
            if not cited:
                held.append(item.text)
                continue
            text = "".join([*held, item.text])
            held.clear()
            if text:
                yield TextDelta(text)
    except LLMError as exc:
        yield Failed(reason=type(exc).__name__)
        return

    if not cited:
        yield TextDelta(no_answer_text)
    yield Sources(tuple(cited.values()))
    yield Done()

