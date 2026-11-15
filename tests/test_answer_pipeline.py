"""The answer pipeline: filter, classify and route, grounding, error handling (AD-1, AD-4, AD-5, AD-7)."""

from collections.abc import Sequence
from datetime import date

import pytest

from app.pipeline.answer import (
    UNKNOWN_CATEGORY_REASON,
    AnswerEvent,
    Done,
    Failed,
    Meta,
    SourceRef,
    Sources,
    Spent,
    TextDelta,
    answer_question,
)
from app.pipeline.filter import REMOVED_MARKER
from app.ports.knowledge_base import Source
from app.ports.llm import AnswerChunk, Exchange, LLMError, LLMRefusalError, Usage
from tests.fakes.fake_llm import CLASSIFY_USAGE, DEFAULT_USAGE, ClassifyCall, ScriptedLLM

NO_ANSWER = "no answer, contact the adviser"
EMBASSY_DECIDES = "only the embassy decides"
FIXED_REPLIES = {"individual_assessment": EMBASSY_DECIDES}
META = Meta(category="general", personal_info_removed=False, clean_question="How much is the fee?")
CLASSIFIED = Spent(CLASSIFY_USAGE, call="classify")


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
    return list(answer_question(question, history, llm, KB, NO_ANSWER, fixed_replies=FIXED_REPLIES))


def _answer(llm: ScriptedLLM, question: str = "q"):  # type: ignore[no-untyped-def]
    return answer_question(question, (), llm, KB, NO_ANSWER, fixed_replies=FIXED_REPLIES)


def test_cited_answer_holds_text_until_the_first_citation() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("", ("s1",)), AnswerChunk("B"), AnswerChunk("C")])

    assert _run(llm) == [
        CLASSIFIED,
        META,
        TextDelta("A"),
        TextDelta("B"),
        TextDelta("C"),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources((_ref("s1"),)),
        Done(),
    ]


def test_held_text_is_released_together_with_the_cited_chunk() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("B"), AnswerChunk("C", ("s1",)), AnswerChunk("D")])

    assert _run(llm)[2:4] == [TextDelta("ABC"), TextDelta("D")]


def test_nothing_is_sent_before_the_first_citation() -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("B")], error=LLMError("boom"))
    events = _answer(llm)

    assert next(events) == CLASSIFIED
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

    sources = next(e for e in _run(llm) if isinstance(e, Sources))

    assert sources == Sources((_ref("s2"), _ref("s1")))
    assert _ref("s3") not in sources.items


def test_empty_text_deltas_are_never_sent() -> None:
    llm = ScriptedLLM([AnswerChunk("", ("s1",)), AnswerChunk(""), AnswerChunk("A"), AnswerChunk("", ("s2",))])

    events = _run(llm)

    assert [e for e in events if isinstance(e, TextDelta)] == [TextDelta("A")]


def test_zero_citations_sends_only_the_no_answer_text() -> None:
    llm = ScriptedLLM([AnswerChunk("uncited guess"), AnswerChunk(" about fees")])

    assert _run(llm) == [
        CLASSIFIED,
        META,
        TextDelta(NO_ANSWER),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources(()),
        Done(),
    ]


def test_empty_answer_gets_the_no_answer_text() -> None:
    assert _run(ScriptedLLM([])) == [
        CLASSIFIED,
        META,
        TextDelta(NO_ANSWER),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources(()),
        Done(),
    ]


def test_personal_info_is_removed_before_the_model_sees_the_question() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])

    events = _run(llm, question="passport AA1234567 what documents?")

    clean = f"passport {REMOVED_MARKER} what documents?"
    assert llm.calls[0].question == clean
    assert events[1] == Meta(category="general", personal_info_removed=True, clean_question=clean)


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
    assert events[1] == META


def test_the_model_is_not_called_before_the_first_event_is_read() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])
    events = _answer(llm)

    assert (llm.classify_calls, llm.calls) == ([], [])
    assert next(events) == CLASSIFIED
    assert isinstance(next(events), Meta)
    # Classified, but not yet answered.
    assert len(llm.classify_calls) == 1
    assert llm.calls == []


@pytest.mark.parametrize(
    ("llm", "reason"),
    [
        (ScriptedLLM([], error=LLMError("boom")), "LLMError"),
        (ScriptedLLM([], refusal=True), "LLMRefusalError"),
    ],
)
def test_error_before_any_text(llm: ScriptedLLM, reason: str) -> None:
    assert _run(llm) == [CLASSIFIED, META, Failed(reason=reason)]


def test_error_after_text_keeps_the_sent_text() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",)), AnswerChunk("B")], error=LLMError("cut"))

    assert _run(llm) == [CLASSIFIED, META, TextDelta("A"), TextDelta("B"), Failed(reason="LLMError")]


def test_unknown_cited_id_is_dropped_and_counted() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",)), AnswerChunk("B", ("not-in-kb",)), AnswerChunk("C")])

    events = _run(llm)

    assert events == [
        CLASSIFIED,
        META,
        TextDelta("A"),
        TextDelta("B"),
        TextDelta("C"),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources((_ref("s1"),), unknown_source_ids=1),
        Done(),
    ]


def test_unknown_id_before_a_known_one_is_dropped_and_text_is_held_until_the_known_one() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("nope", "s2")), AnswerChunk("B", ("s1", "nope", "other"))])

    events = _run(llm)

    assert events == [
        CLASSIFIED,
        META,
        TextDelta("A"),
        TextDelta("B"),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources((_ref("s2"), _ref("s1")), unknown_source_ids=2),
        Done(),
    ]


def test_only_unknown_ids_give_the_no_answer_text() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("nope",)), AnswerChunk("B", ("nope", "other"))])

    events = _run(llm)

    assert events == [
        CLASSIFIED,
        META,
        TextDelta(NO_ANSWER),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources((), unknown_source_ids=2),
        Done(),
    ]


def test_no_unknown_ids_counts_zero() -> None:
    events = _run(ScriptedLLM([AnswerChunk("A", ("s1",))]))

    assert events[-2] == Sources((_ref("s1"),), unknown_source_ids=0)


def test_usage_ends_the_answer() -> None:
    usage = Usage(input_tokens=1, output_tokens=1, cache_read_tokens=0, cache_write_tokens=0)

    class AfterUsage(ScriptedLLM):
        def _stream(self):  # type: ignore[override]
            yield AnswerChunk("A", ("s1",))
            yield usage
            yield AnswerChunk("ignored", ("s2",))

    assert _run(AfterUsage()) == [
        CLASSIFIED,
        META,
        TextDelta("A"),
        Spent(usage, call="answer"),
        Sources((_ref("s1"),)),
        Done(),
    ]


def test_spent_carries_the_usage_the_model_reported() -> None:
    usage = Usage(input_tokens=1000, output_tokens=200, cache_read_tokens=50000, cache_write_tokens=0)

    events = _run(ScriptedLLM([AnswerChunk("A", ("s1",))], usage=usage))

    assert events[-3:] == [Spent(usage, call="answer"), Sources((_ref("s1"),)), Done()]


def test_no_spent_without_usage() -> None:
    class NoUsage(ScriptedLLM):
        def _stream(self):  # type: ignore[override]
            yield AnswerChunk("A", ("s1",))

    assert _run(NoUsage()) == [CLASSIFIED, META, TextDelta("A"), Sources((_ref("s1"),)), Done()]


def test_no_answer_spent_on_error() -> None:
    events = _run(ScriptedLLM([AnswerChunk("A", ("s1",))], error=LLMError("cut")))

    # Only the classify call reported its usage.
    assert [e for e in events if isinstance(e, Spent)] == [CLASSIFIED]


def test_failed_is_always_last() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))], error=LLMError("cut"))

    events = _run(llm)

    assert isinstance(events[-1], Failed)
    assert not any(isinstance(e, (Sources, Done)) for e in events)


# --- classify and route (Story 2.1) ----------------------------------------------------


def test_general_question_is_classified_then_answered() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))], category="general")

    events = _run(llm)

    assert events[:2] == [CLASSIFIED, META]
    assert len(llm.calls) == 1
    assert llm.classify_calls == [ClassifyCall("How much is the fee?", ())]


def test_individual_assessment_gets_the_fixed_reply_and_no_answer_call() -> None:
    llm = ScriptedLLM([AnswerChunk("a guess about your chances", ("s1",))], category="individual_assessment")

    events = _run(llm, question="Will I get the visa?")

    assert events == [
        CLASSIFIED,
        Meta(
            category="individual_assessment",
            personal_info_removed=False,
            clean_question="Will I get the visa?",
        ),
        TextDelta(EMBASSY_DECIDES),
        Sources(()),
        Done(),
    ]
    assert llm.calls == []


def test_classifier_gets_only_the_last_two_cleaned_exchanges() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))])
    history = [
        Exchange("oldest question", "oldest answer"),
        Exchange("which documents? passport AA1234567", "These documents."),
        Exchange("and the form?", "This form."),
    ]

    _run(llm, question="and the fee?", history=history)

    assert llm.classify_calls == [
        ClassifyCall(
            "and the fee?",
            (
                Exchange(f"which documents? passport {REMOVED_MARKER}", "These documents."),
                Exchange("and the form?", "This form."),
            ),
        )
    ]
    # The answer call still gets the whole cleaned history.
    assert len(llm.calls[0].history) == 3


def test_classifier_sees_only_the_cleaned_question() -> None:
    llm = ScriptedLLM(category="individual_assessment")

    events = _run(llm, question="passport AA1234567 will I get the visa?")

    clean = f"passport {REMOVED_MARKER} will I get the visa?"
    assert llm.classify_calls[0].question == clean
    assert events[1] == Meta(
        category="individual_assessment", personal_info_removed=True, clean_question=clean
    )


@pytest.mark.parametrize("category", ["done"])
def test_categories_not_built_yet_are_answered_as_general(category: str) -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))], category=category)

    events = _run(llm)

    assert events == [
        CLASSIFIED,
        META,
        TextDelta("A"),
        Spent(DEFAULT_USAGE, call="answer"),
        Sources((_ref("s1"),)),
        Done(),
    ]
    assert len(llm.calls) == 1


@pytest.mark.parametrize(
    ("error", "reason"),
    [(LLMError("boom"), "LLMError"), (LLMRefusalError("no"), "LLMRefusalError")],
)
def test_classify_error_fails_before_meta_and_answers_nothing(error: LLMError, reason: str) -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))], classify_error=error)

    assert _run(llm) == [Failed(reason=reason)]
    assert llm.calls == []


def test_category_outside_the_set_fails_after_its_usage_and_answers_nothing() -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("s1",))], category="weather")

    events = _run(llm)

    assert events == [CLASSIFIED, Failed(reason=UNKNOWN_CATEGORY_REASON)]
    assert "weather" not in repr(events)
    assert llm.calls == []
