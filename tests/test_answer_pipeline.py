"""The answer pipeline: filter, grounding rule and error handling (AD-1, AD-4, AD-7)."""

from collections.abc import Sequence
from datetime import date

import pytest

from app.pipeline.answer import (
    AnswerEvent,
    Done,
    Failed,
    Meta,
    SourceRef,
    Sources,
    TextDelta,
    answer_question,
)
from app.pipeline.filter import REMOVED_MARKER
from app.ports.knowledge_base import Source
from app.ports.llm import AnswerChunk, Exchange, LLMError, Usage
from tests.fakes.fake_llm import ScriptedLLM

NO_ANSWER = "no answer, contact the adviser"
META = Meta(category="general", personal_info_removed=False, clean_question="How much is the fee?")


def _source(sid: str) -> Source:
    return Source(
        id=sid,
        title=f"Title {sid}",
        url=f"https://www.udi.no/{sid}",
        publisher="UDI",
        retrieved=date(2026, 11, 1),
        text=f"text of {sid}",
    )


class StandInKnowledgeBase:
    def __init__(self, *ids: str) -> None:
        self._sources = {sid: _source(sid) for sid in ids}

    def documents(self) -> Sequence[Source]:
        return tuple(self._sources[sid] for sid in sorted(self._sources))

    def source(self, source_id: str) -> Source:
        return self._sources[source_id]


KB = StandInKnowledgeBase("s1", "s2", "s3")


def _ref(sid: str) -> SourceRef:
    return SourceRef(sid, f"Title {sid}", f"https://www.udi.no/{sid}")


def _run(
    llm: ScriptedLLM,
    question: str = "How much is the fee?",
    history: Sequence[Exchange] = (),
) -> list[AnswerEvent]:
    return list(answer_question(question, history, llm, KB, NO_ANSWER))


def test_cited_answer_holds_text_until_the_first_citation() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("", ("s1",)), AnswerChunk("B"), AnswerChunk("C")])

    assert _run(llm) == [
        META,
        TextDelta("A"),
        TextDelta("B"),
        TextDelta("C"),
        Sources((_ref("s1"),)),
        Done(),
    ]


def test_held_text_is_released_together_with_the_cited_chunk() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("B"), AnswerChunk("C", ("s1",)), AnswerChunk("D")])

    assert _run(llm)[1:3] == [TextDelta("ABC"), TextDelta("D")]


def test_nothing_is_sent_before_the_first_citation() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("B")], error=LLMError("boom"))
    events = answer_question("q", (), llm, KB, NO_ANSWER)

    assert isinstance(next(events), Meta)
    # The model has written text, but none of it is released without a citation.
    assert list(events) == [Failed(reason="LLMError")]


def test_sources_are_the_cited_ones_in_first_cited_order_each_once() -> None:
    llm = ScriptedLLM(
        [
            AnswerChunk("x", ("s2",)),
            AnswerChunk("y", ("s1", "s2")),
            AnswerChunk("z", ("s2",)),
        ]
    )

    events = _run(llm)

    assert events[-2] == Sources((_ref("s2"), _ref("s1")))
    assert _ref("s3") not in events[-2].items


def test_empty_text_deltas_are_never_sent() -> None:
    llm = ScriptedLLM([AnswerChunk("", ("s1",)), AnswerChunk(""), AnswerChunk("A"), AnswerChunk("", ("s2",))])

    events = _run(llm)

    assert [e for e in events if isinstance(e, TextDelta)] == [TextDelta("A")]


def test_zero_citations_sends_only_the_no_answer_text() -> None:
    llm = ScriptedLLM([AnswerChunk("uncited guess"), AnswerChunk(" about fees")])

    assert _run(llm) == [META, TextDelta(NO_ANSWER), Sources(()), Done()]


def test_empty_answer_gets_the_no_answer_text() -> None:
    assert _run(ScriptedLLM([])) == [META, TextDelta(NO_ANSWER), Sources(()), Done()]


def test_personal_info_is_removed_before_the_model_sees_the_question() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])

    events = _run(llm, question="passport AA1234567 what documents?")

    clean = f"passport {REMOVED_MARKER} what documents?"
    assert llm.calls[0].question == clean
    assert events[0] == Meta(category="general", personal_info_removed=True, clean_question=clean)


def test_history_is_filtered_but_does_not_set_the_flag() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])
    history = [
        Exchange("my id is 1234567890123, which form?", "Use the form."),
        Exchange("thanks", "passport AB1234567 noted"),
    ]

    events = _run(llm, history=history)

    assert llm.calls[0].history == (
        Exchange(f"my id is {REMOVED_MARKER}, which form?", "Use the form."),
        Exchange("thanks", f"passport {REMOVED_MARKER} noted"),
    )
    assert events[0] == META


def test_the_model_is_not_called_before_the_first_event_is_read() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])
    events = answer_question("q", (), llm, KB, NO_ANSWER)

    assert llm.calls == []
    next(events)  # Meta comes from the filter alone
    assert llm.calls == []


@pytest.mark.parametrize(
    ("llm", "reason"),
    [
        (ScriptedLLM([], error=LLMError("boom")), "LLMError"),
        (ScriptedLLM([], refusal=True), "LLMRefusalError"),
    ],
)
def test_error_before_any_text(llm: ScriptedLLM, reason: str) -> None:
    assert _run(llm) == [META, Failed(reason=reason)]


def test_error_after_text_keeps_the_sent_text() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",)), AnswerChunk("B")], error=LLMError("cut"))

    assert _run(llm) == [META, TextDelta("A"), TextDelta("B"), Failed(reason="LLMError")]


def test_unknown_cited_id_fails() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",)), AnswerChunk("B", ("not-in-kb",)), AnswerChunk("C")])

    events = _run(llm)

    assert events == [META, TextDelta("A"), Failed(reason="unknown source id")]


def test_usage_ends_the_answer() -> None:
    usage = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)

    class AfterUsage(ScriptedLLM):
        def _stream(self):  # type: ignore[override]
            yield AnswerChunk("A", ("s1",))
            yield usage
            yield AnswerChunk("ignored", ("s2",))

    assert _run(AfterUsage()) == [META, TextDelta("A"), Sources((_ref("s1"),)), Done()]


def test_failed_is_always_last() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("nope",))])

    events = _run(llm)

    assert isinstance(events[-1], Failed)
    assert not any(isinstance(e, (Sources, Done)) for e in events)
