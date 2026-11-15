"""The Anthropic adapter, with stand-in clients and a stand-in transport. Never touches the network."""

import json
from collections.abc import Iterator, Sequence
from datetime import date
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx2
import pytest
from pydantic import SecretStr

from app.adapters.anthropic_llm import MAX_TOKENS_ANSWER, AnthropicLLM, build_answer_request
from app.adapters.file_prompts import Prompt
from app.config import Settings
from app.ports.knowledge_base import Source
from app.ports.llm import AnswerChunk, Exchange, LLMClient, LLMError, LLMRefusalError, Usage

PROMPT = Prompt(version="test-1", text="Answer in Thai from the documents.")


def _source(sid: str) -> Source:
    return Source(
        id=sid,
        title=f"Title of {sid}",
        url=f"https://www.udi.no/en/{sid}/",
        publisher="UDI",
        retrieved=date(2026, 11, 13),
        text=f"Text of {sid}.",
    )


# Already sorted by id, as `KnowledgeBase.documents()` promises.
DOCUMENTS = (_source("a-steps"), _source("b-fees"), _source("c-sponsor"))


class StandInKnowledgeBase:
    def documents(self) -> Sequence[Source]:
        return DOCUMENTS

    def source(self, source_id: str) -> Source:
        return {s.id: s for s in DOCUMENTS}[source_id]


# --- stand-in SDK client -------------------------------------------------------


def _text(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="content_block_delta", delta=SimpleNamespace(type="text_delta", text=text))


def _cite(index: int) -> SimpleNamespace:
    citation = SimpleNamespace(type="char_location", document_index=index, cited_text="x")
    return SimpleNamespace(
        type="content_block_delta", delta=SimpleNamespace(type="citations_delta", citation=citation)
    )


def _thinking(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        type="content_block_delta", delta=SimpleNamespace(type="thinking_delta", thinking=text)
    )


def _other(kind: str) -> SimpleNamespace:
    return SimpleNamespace(type=kind)


def _final(
    stop_reason: str = "end_turn", cache_read: int | None = 0, cache_write: int | None = 0
) -> SimpleNamespace:
    usage = SimpleNamespace(
        input_tokens=1200,
        output_tokens=300,
        cache_read_input_tokens=cache_read,
        cache_creation_input_tokens=cache_write,
    )
    return SimpleNamespace(stop_reason=stop_reason, usage=usage)


class StandInStream:
    def __init__(self, events: list[Any], final: Any, error: Exception | None) -> None:
        self.events = events
        self.final = final
        self.error = error
        self.closed = False

    def __enter__(self) -> "StandInStream":
        return self

    def __exit__(self, *exc: object) -> None:
        self.closed = True

    def __iter__(self) -> Iterator[Any]:
        yield from self.events
        if self.error is not None:
            raise self.error

    def get_final_message(self) -> Any:
        return self.final


class StandInClient:
    """Records the request; plays back events, then the final message, or raises."""

    def __init__(
        self,
        events: list[Any] = (),  # type: ignore[assignment]
        final: Any = None,
        open_error: Exception | None = None,
        stream_error: Exception | None = None,
    ) -> None:
        self.requests: list[dict[str, Any]] = []
        self.stream: StandInStream | None = None
        self._events = list(events)
        self._final = final if final is not None else _final()
        self._open_error = open_error
        self._stream_error = stream_error
        self.messages = SimpleNamespace(stream=self._open)

    def _open(self, **kwargs: Any) -> StandInStream:
        self.requests.append(kwargs)
        if self._open_error is not None:
            raise self._open_error
        self.stream = StandInStream(self._events, self._final, self._stream_error)
        return self.stream


def _llm(client: Any, settings: Settings) -> AnthropicLLM:
    return AnthropicLLM(settings, StandInKnowledgeBase(), PROMPT, client=client)


# --- request shape ----------------------------------------------------------------


def _request(question: str = "คำถาม", history: Sequence[Exchange] = ()) -> dict[str, Any]:
    return build_answer_request(
        model="claude-opus-5-5",
        effort="medium",
        system=PROMPT.text,
        documents=DOCUMENTS,
        question=question,
        history=history,
    )


def test_request_has_model_thinking_effort_and_no_sampling_keys() -> None:
    request = _request()

    assert request["model"] == "claude-opus-5-5"
    assert request["max_tokens"] == MAX_TOKENS_ANSWER == 32000
    assert request["thinking"] == {"type": "adaptive"}
    assert request["output_config"] == {"effort": "medium"}
    assert request["system"] == PROMPT.text
    assert not {"temperature", "top_p", "top_k", "betas"} & set(request)


def test_request_without_history_puts_documents_then_question_in_one_turn() -> None:
    messages = _request("ต้องเตรียมเอกสารอะไรบ้าง")["messages"]

    assert len(messages) == 1
    assert messages[0]["role"] == "user"
    content = messages[0]["content"]
    assert [block["type"] for block in content] == ["document"] * 3 + ["text"]
    assert content[-1] == {"type": "text", "text": "ต้องเตรียมเอกสารอะไรบ้าง"}


def test_documents_keep_order_and_all_have_citations_on() -> None:
    documents = _request()["messages"][0]["content"][:-1]

    assert [d["title"] for d in documents] == [s.title for s in DOCUMENTS]
    for block, source in zip(documents, DOCUMENTS, strict=True):
        assert block["source"] == {"type": "text", "media_type": "text/plain", "data": source.text}
        assert block["citations"] == {"enabled": True}


def test_exactly_one_cache_breakpoint_on_the_last_document() -> None:
    request = _request(history=[Exchange("q1", "a1")])

    marked = [
        (m, i)
        for m, message in enumerate(request["messages"])
        if isinstance(message["content"], list)
        for i, block in enumerate(message["content"])
        if "cache_control" in block
    ]
    assert marked == [(0, len(DOCUMENTS) - 1)]
    assert request["messages"][0]["content"][len(DOCUMENTS) - 1]["cache_control"] == {"type": "ephemeral"}


def test_history_alternates_as_plain_text_and_question_comes_last() -> None:
    history = [Exchange("q1", "a1"), Exchange("q2", "a2")]

    messages = _request("q3", history)["messages"]

    assert [m["role"] for m in messages] == ["user", "assistant", "user", "assistant", "user"]
    assert messages[0]["content"][-1] == {"type": "text", "text": "q1"}
    assert [m["content"] for m in messages[1:]] == ["a1", "q2", "a2", "q3"]
    # Documents only in the first user turn.
    assert all(b["type"] == "document" for b in messages[0]["content"][:-1])


def test_request_with_the_same_input_is_identical() -> None:
    assert _request("q", [Exchange("a", "b")]) == _request("q", [Exchange("a", "b")])


def test_request_needs_documents() -> None:
    with pytest.raises(LLMError):
        build_answer_request(model="m", effort="low", system="s", documents=(), question="q", history=())


def test_adapter_sends_settings_and_documents_from_the_knowledge_base(settings: Settings) -> None:
    client = StandInClient(events=[_text("x"), _cite(0)])
    settings = settings.model_copy(update={"model_answer": "model-x", "effort_answer": "high"})

    list(_llm(client, settings).answer("q", []))

    assert client.requests == [
        build_answer_request(
            model="model-x", effort="high", system=PROMPT.text, documents=DOCUMENTS, question="q", history=()
        )
    ]


# --- event mapping ------------------------------------------------------------------


def test_cited_answer_maps_text_and_citation_then_usage(settings: Settings) -> None:
    client = StandInClient(
        events=[
            _other("message_start"),
            _thinking("hmm"),
            _text("ค่าธรรมเนียม"),
            _cite(2),
            _text(" 90 ยูโร"),
            _other("content_block_stop"),
            _other("message_delta"),
            _other("message_stop"),
        ],
        final=_final(cache_read=None, cache_write=4000),
    )

    result = list(_llm(client, settings).answer("q", []))

    assert result == [
        AnswerChunk("ค่าธรรมเนียม", ()),
        AnswerChunk("", ("c-sponsor",)),
        AnswerChunk(" 90 ยูโร", ()),
        Usage(input_tokens=1200, output_tokens=300, cache_read_tokens=0, cache_write_tokens=4000),
    ]
    assert client.stream is not None and client.stream.closed


class UnsortedKnowledgeBase(StandInKnowledgeBase):
    def documents(self) -> Sequence[Source]:
        return (DOCUMENTS[2], DOCUMENTS[0], DOCUMENTS[1])


def test_adapter_sorts_documents_by_id_for_request_and_citations(settings: Settings) -> None:
    client = StandInClient(events=[_text("x"), _cite(0)])
    llm = AnthropicLLM(settings, UnsortedKnowledgeBase(), PROMPT, client=client)

    result = list(llm.answer("q", []))

    titles = [b["title"] for b in client.requests[0]["messages"][0]["content"][:-1]]
    assert titles == [s.title for s in DOCUMENTS]
    assert result[1] == AnswerChunk("", ("a-steps",))


@pytest.mark.parametrize("cache_write", [None, 0])
def test_missing_cache_write_count_is_zero(settings: Settings, cache_write: int | None) -> None:
    client = StandInClient(events=[_text("a")], final=_final(cache_read=5, cache_write=cache_write))

    usage = list(_llm(client, settings).answer("q", []))[-1]

    assert usage == Usage(input_tokens=1200, output_tokens=300, cache_read_tokens=5, cache_write_tokens=0)


def test_uncited_answer_has_only_empty_source_ids(settings: Settings) -> None:
    client = StandInClient(events=[_text("a"), _text("b")])

    result = list(_llm(client, settings).answer("q", []))

    assert [type(item) for item in result] == [AnswerChunk, AnswerChunk, Usage]
    assert all(chunk.source_ids == () for chunk in result[:-1])


@pytest.mark.parametrize("index", [3, -1, None])
def test_citation_of_unknown_document_raises(settings: Settings, index: int | None) -> None:
    client = StandInClient(events=[_cite(index)])  # type: ignore[arg-type]

    with pytest.raises(LLMError):
        list(_llm(client, settings).answer("q", []))


def test_refusal_raises_refusal_error(settings: Settings) -> None:
    client = StandInClient(events=[_text("a")], final=_final("refusal"))

    with pytest.raises(LLMRefusalError):
        list(_llm(client, settings).answer("q", []))


@pytest.mark.parametrize("stop_reason", ["max_tokens", "model_context_window_exceeded", "pause_turn"])
def test_cut_off_answer_raises(settings: Settings, stop_reason: str) -> None:
    client = StandInClient(events=[_text("a")], final=_final(stop_reason))

    with pytest.raises(LLMError) as raised:
        list(_llm(client, settings).answer("q", []))
    assert not isinstance(raised.value, LLMRefusalError)


def _request_obj() -> httpx2.Request:
    return httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


SDK_ERRORS = [
    anthropic.APIConnectionError(request=_request_obj()),
    anthropic.APITimeoutError(request=_request_obj()),
    anthropic.BadRequestError("bad", response=httpx2.Response(400, request=_request_obj()), body=None),
    anthropic.InternalServerError("down", response=httpx2.Response(500, request=_request_obj()), body=None),
]


@pytest.mark.parametrize("error", SDK_ERRORS, ids=lambda e: type(e).__name__)
def test_sdk_error_on_open_becomes_llm_error(settings: Settings, error: Exception) -> None:
    client = StandInClient(open_error=error)

    with pytest.raises(LLMError) as raised:
        list(_llm(client, settings).answer("q", []))
    assert raised.value.__cause__ is error


@pytest.mark.parametrize(
    "error",
    [*SDK_ERRORS, httpx2.ReadError("connection dropped")],
    ids=lambda e: type(e).__name__,
)
def test_error_mid_stream_becomes_llm_error(settings: Settings, error: Exception) -> None:
    client = StandInClient(events=[_text("a")], stream_error=error)
    stream = _llm(client, settings).answer("q", [])

    assert next(stream) == AnswerChunk("a", ())
    with pytest.raises(LLMError) as raised:
        next(stream)
    assert raised.value.__cause__ is error
    assert client.stream is not None and client.stream.closed


def test_construction_needs_no_key_and_no_network(settings: Settings) -> None:
    llm: LLMClient = AnthropicLLM(settings, StandInKnowledgeBase(), PROMPT)
    assert llm is not None


def test_sdk_client_is_built_once_from_the_key(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    settings = settings.model_copy(update={"anthropic_api_key": SecretStr("sk-test")})
    llm = AnthropicLLM(settings, StandInKnowledgeBase(), PROMPT)

    client = llm._sdk_client()
    assert isinstance(client, anthropic.Anthropic)
    assert client.api_key == "sk-test"
    assert llm._sdk_client() is client

    # Every answer call goes through that client: only its stream is replaced (no network).
    calls: list[dict[str, Any]] = []

    def stream(**kwargs: Any) -> StandInStream:
        calls.append(kwargs)
        return StandInStream([_text("a")], _final(), None)

    monkeypatch.setattr(client.messages, "stream", stream)
    list(llm.answer("q", []))
    list(llm.answer("q", []))
    assert len(calls) == 2


def test_answer_without_key_raises_llm_error(settings: Settings) -> None:
    llm = AnthropicLLM(settings, StandInKnowledgeBase(), PROMPT)

    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        list(llm.answer("q", []))


@pytest.mark.parametrize("method, args", [("classify", ("q", [])), ("translate", ("t",))])
def test_later_methods_are_not_implemented_yet(settings: Settings, method: str, args: tuple) -> None:
    with pytest.raises(NotImplementedError):
        getattr(AnthropicLLM(settings, StandInKnowledgeBase(), PROMPT), method)(*args)


# --- the real SDK over a stand-in transport ------------------------------------------


def _sse(events: list[dict[str, Any]]) -> bytes:
    return "".join(f"event: {e['type']}\ndata: {json.dumps(e)}\n\n" for e in events).encode()


def _sse_answer(stop_reason: str = "end_turn") -> bytes:
    return _sse(
        [
            {
                "type": "message_start",
                "message": {
                    "id": "msg_1",
                    "type": "message",
                    "role": "assistant",
                    "model": "claude-opus-5-5",
                    "content": [],
                    "stop_reason": None,
                    "stop_sequence": None,
                    "usage": {
                        "input_tokens": 50,
                        "output_tokens": 1,
                        "cache_read_input_tokens": 7000,
                        "cache_creation_input_tokens": 0,
                    },
                },
            },
            {
                "type": "content_block_start",
                "index": 0,
                "content_block": {"type": "thinking", "thinking": "", "signature": ""},
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "thinking_delta", "thinking": "plan"},
            },
            {
                "type": "content_block_delta",
                "index": 0,
                "delta": {"type": "signature_delta", "signature": "sig"},
            },
            {"type": "content_block_stop", "index": 0},
            {
                "type": "content_block_start",
                "index": 1,
                "content_block": {"type": "text", "text": "", "citations": []},
            },
            {
                "type": "content_block_delta",
                "index": 1,
                "delta": {"type": "text_delta", "text": "ค่าธรรมเนียม 90 ยูโร"},
            },
            {
                "type": "content_block_delta",
                "index": 1,
                "delta": {
                    "type": "citations_delta",
                    "citation": {
                        "type": "char_location",
                        "cited_text": "Text of b-fees.",
                        "document_index": 1,
                        "document_title": "Title of b-fees",
                        "start_char_index": 0,
                        "end_char_index": 15,
                    },
                },
            },
            {"type": "content_block_stop", "index": 1},
            {
                "type": "message_delta",
                "delta": {"type": "message_delta", "stop_reason": stop_reason, "stop_sequence": None},
                "usage": {"output_tokens": 120},
            },
            {"type": "message_stop"},
        ]
    )


def _sdk_client(handler: Any) -> anthropic.Anthropic:
    return anthropic.Anthropic(
        api_key="test-key",
        max_retries=0,
        http_client=httpx2.Client(transport=httpx2.MockTransport(handler)),
    )


def test_real_sdk_events_map_to_chunks_and_usage(settings: Settings) -> None:
    sent: list[dict[str, Any]] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        sent.append(json.loads(request.content))
        return httpx2.Response(200, headers={"content-type": "text/event-stream"}, content=_sse_answer())

    result = list(_llm(_sdk_client(handler), settings).answer("q", [Exchange("q0", "a0")]))

    assert result == [
        AnswerChunk("ค่าธรรมเนียม 90 ยูโร", ()),
        AnswerChunk("", ("b-fees",)),
        Usage(input_tokens=50, output_tokens=120, cache_read_tokens=7000, cache_write_tokens=0),
    ]
    body = sent[0]
    assert body["model"] == settings.model_answer
    assert body["thinking"] == {"type": "adaptive"}
    assert body["output_config"] == {"effort": settings.effort_answer}
    assert body["stream"] is True
    assert [m["role"] for m in body["messages"]] == ["user", "assistant", "user"]


def test_real_sdk_refusal_raises_refusal_error(settings: Settings) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(
            200, headers={"content-type": "text/event-stream"}, content=_sse_answer("refusal")
        )

    with pytest.raises(LLMRefusalError):
        list(_llm(_sdk_client(handler), settings).answer("q", []))


@pytest.mark.parametrize("status", [401, 429, 500, 529])
def test_real_sdk_status_error_becomes_llm_error(settings: Settings, status: int) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(status, json={"type": "error", "error": {"type": "x", "message": "no"}})

    with pytest.raises(LLMError) as raised:
        list(_llm(_sdk_client(handler), settings).answer("q", []))
    assert isinstance(raised.value.__cause__, anthropic.APIStatusError)


def test_real_sdk_connection_error_becomes_llm_error(settings: Settings) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        raise httpx2.ConnectError("no route", request=request)

    with pytest.raises(LLMError) as raised:
        list(_llm(_sdk_client(handler), settings).answer("q", []))
    assert isinstance(raised.value.__cause__, anthropic.APIConnectionError)
