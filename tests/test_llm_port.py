import dataclasses
import inspect
from typing import get_args

import pytest

from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.ollama_llm import OllamaLLM
from app.ports.llm import (
    AnswerChunk,
    Category,
    Exchange,
    LLMClient,
    LLMError,
    LLMRefusalError,
    Usage,
)
from tests.fakes.fake_llm import CLASSIFY_USAGE, DEFAULT_USAGE, AnswerCall, ClassifyCall, ScriptedLLM

USAGE = Usage(input_tokens=10, output_tokens=5, cache_read_tokens=3, cache_write_tokens=2)


def test_categories_are_the_closed_set_of_ad_5() -> None:
    assert set(get_args(Category)) == {
        "general",
        "individual_assessment",
        "out_of_scope",
        "reach_person",
        "done",
    }


@pytest.mark.parametrize(
    "value",
    [Exchange("q", "a"), AnswerChunk("text", ("src",)), USAGE],
)
def test_port_values_are_frozen(value: object) -> None:
    field = dataclasses.fields(value)[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(value, field, "changed")


def test_answer_chunk_has_no_sources_by_default() -> None:
    assert AnswerChunk("text").source_ids == ()


def test_refusal_is_an_llm_error() -> None:
    assert issubclass(LLMRefusalError, LLMError)


def _parameters(cls: type, method: str) -> list[str]:
    return list(inspect.signature(getattr(cls, method)).parameters)


@pytest.mark.parametrize("implementation", [ScriptedLLM, AnthropicLLM, OllamaLLM])
@pytest.mark.parametrize("method", ["answer", "classify", "translate"])
def test_implementations_match_the_port_signatures(implementation: type, method: str) -> None:
    assert _parameters(implementation, method) == _parameters(LLMClient, method)


def test_fake_yields_the_script_then_usage() -> None:
    chunks = [AnswerChunk("สวัสดี"), AnswerChunk("", ("udi-fees",)), AnswerChunk(" ครับ")]
    llm = ScriptedLLM(chunks=chunks, usage=USAGE)

    assert list(llm.answer("q", [])) == [*chunks, USAGE]


def test_fake_without_chunks_yields_only_usage() -> None:
    assert list(ScriptedLLM().answer("q", [])) == [DEFAULT_USAGE]


def test_fake_raises_scripted_error_after_the_chunks() -> None:
    error = LLMError("boom")
    stream = ScriptedLLM(chunks=[AnswerChunk("a")], error=error).answer("q", [])

    assert next(stream) == AnswerChunk("a")
    with pytest.raises(LLMError) as raised:
        next(stream)
    assert raised.value is error


def test_fake_refusal_raises_refusal_error() -> None:
    stream = ScriptedLLM(refusal=True).answer("q", [])

    with pytest.raises(LLMRefusalError):
        list(stream)


def test_fake_records_calls_when_called() -> None:
    llm = ScriptedLLM()
    history = [Exchange("q1", "a1")]

    llm.answer("q2", history)  # not read: still recorded

    assert llm.calls == [AnswerCall("q2", (Exchange("q1", "a1"),))]


def test_fake_classifies_as_scripted_and_records_the_call() -> None:
    llm = ScriptedLLM(category="individual_assessment", classify_usage=USAGE)

    assert llm.classify("will I get it?", [Exchange("q1", "a1")]) == ("individual_assessment", USAGE)
    assert llm.classify_calls == [ClassifyCall("will I get it?", (Exchange("q1", "a1"),))]
    assert llm.calls == []


def test_fake_classifies_as_general_by_default() -> None:
    assert ScriptedLLM().classify("q", []) == ("general", CLASSIFY_USAGE)


def test_fake_raises_the_scripted_classify_error() -> None:
    error = LLMRefusalError("no")
    llm = ScriptedLLM(classify_error=error)

    with pytest.raises(LLMRefusalError) as raised:
        llm.classify("q", [])
    assert raised.value is error
    assert len(llm.classify_calls) == 1


def test_fake_translate_is_not_implemented_yet() -> None:
    with pytest.raises(NotImplementedError):
        ScriptedLLM().translate("t")
