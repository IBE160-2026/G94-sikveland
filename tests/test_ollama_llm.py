"""The Ollama adapter, with a stand-in transport (`httpx.MockTransport`). Never touches the network."""

import json
import logging
from collections.abc import Callable, Iterator, Sequence
from datetime import date
from typing import Any

import httpx
import pytest

from app.adapters.file_prompts import Prompt
from app.adapters.ollama_llm import (
    MAX_MARKER_BODY,
    TIMEOUT,
    MarkerParser,
    OllamaLLM,
    build_chat_request,
    build_system_prompt,
)
from app.config import Settings
from app.ports.knowledge_base import Source
from app.ports.llm import AnswerChunk, Exchange, LLMClient, LLMError, Usage

PROMPT = Prompt(version="a-1", text="Answer in Thai from the documents.")
CITING = Prompt(version="c-1", text="Cite as [[id]].")
BASE_URL = "http://ollama.test:11434"


def _source(sid: str) -> Source:
    return Source(
        id=sid,
        title=f'Title "of" {sid}',
        url=f"https://www.udi.no/en/{sid}/",
        publisher="UDI",
        retrieved=date(2026, 11, 13),
        text=f"Text of {sid}.",
    )


DOCUMENTS = (_source("a-steps"), _source("b-fees"), _source("c-sponsor"))


class StandInKnowledgeBase:
    def __init__(self, documents: Sequence[Source] = DOCUMENTS) -> None:
        self._documents = tuple(documents)

    def documents(self) -> Sequence[Source]:
        return self._documents

    def source(self, source_id: str) -> Source:
        return {s.id: s for s in self._documents}[source_id]


# --- stand-in Ollama server ---------------------------------------------------------


def _content(text: str) -> dict[str, Any]:
    return {"model": "m", "message": {"role": "assistant", "content": text}, "done": False}


def _thinking(text: str) -> dict[str, Any]:
    return {"model": "m", "message": {"role": "assistant", "content": "", "thinking": text}, "done": False}


def _final(done_reason: str = "stop", prompt_eval_count: Any = 1200, eval_count: Any = 300) -> dict[str, Any]:
    line: dict[str, Any] = {
        "model": "m",
        "message": {"role": "assistant", "content": ""},
        "done": True,
        "done_reason": done_reason,
    }
    if prompt_eval_count is not None:
        line["prompt_eval_count"] = prompt_eval_count
    if eval_count is not None:
        line["eval_count"] = eval_count
    return line


def _body(*lines: dict[str, Any] | str) -> bytes:
    return "".join(
        (json.dumps(x, ensure_ascii=False) if isinstance(x, dict) else x) + "\n" for x in lines
    ).encode()


def _stream(*pieces: str, final: dict[str, Any] | None = None) -> bytes:
    return _body(*(_content(p) for p in pieces), final if final is not None else _final())


class Server:
    """Answers every request with `body` and `status`, and records the requests."""

    def __init__(self, body: bytes = b"", status: int = 200, error: Exception | None = None) -> None:
        self.body = body
        self.status = status
        self.error = error
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return httpx.Response(self.status, content=self.body)

    def json(self, index: int = -1) -> dict[str, Any]:
        return json.loads(self.requests[index].content)


@pytest.fixture
def ollama_settings(settings: Settings) -> Settings:
    return settings.model_copy(update={"llm_provider": "ollama", "ollama_base_url": BASE_URL + "/"})


def _llm(settings: Settings, server: Callable[[httpx.Request], httpx.Response], **kb: Any) -> OllamaLLM:
    client = httpx.Client(transport=httpx.MockTransport(server))
    return OllamaLLM(settings, StandInKnowledgeBase(**kb), PROMPT, CITING, client=client)


def _answer(
    llm: OllamaLLM, question: str = "q", history: Sequence[Exchange] = ()
) -> list[AnswerChunk | Usage]:
    return list(llm.answer(question, history))


def _split(items: list[AnswerChunk | Usage]) -> tuple[str, list[str], list[Usage]]:
    chunks = [i for i in items if isinstance(i, AnswerChunk)]
    return (
        "".join(c.text for c in chunks),
        [sid for c in chunks for sid in c.source_ids],
        [i for i in items if isinstance(i, Usage)],
    )


def _parse(*pieces: str) -> list[AnswerChunk]:
    parser = MarkerParser()
    out = [parser.feed(p) for p in pieces] + [parser.finish()]
    return [c for c in out if c is not None]


# --- request ------------------------------------------------------------------------


def test_satisfies_the_port(ollama_settings: Settings) -> None:
    llm: LLMClient = _llm(ollama_settings, Server(_stream("x")))
    assert llm is not None


def test_building_needs_no_network(ollama_settings: Settings) -> None:
    llm = OllamaLLM(ollama_settings, StandInKnowledgeBase(), PROMPT, CITING)

    timeout = llm._client.timeout
    assert timeout.connect is not None and timeout.connect <= 10
    assert timeout.read is not None and timeout.read >= 120
    assert timeout == TIMEOUT


def test_request_goes_to_api_chat_with_think_num_ctx_and_stream(ollama_settings: Settings) -> None:
    server = Server(_stream("x"))
    settings = ollama_settings.model_copy(update={"ollama_model": "qwen-test", "ollama_num_ctx": 40000})

    _answer(_llm(settings, server), "How much?")

    [request] = server.requests
    assert request.method == "POST"
    assert str(request.url) == BASE_URL + "/api/chat"
    body = server.json()
    assert body["model"] == "qwen-test"
    assert body["stream"] is True
    assert body["think"] is True
    assert body["options"] == {"num_ctx": 40000}
    assert body["messages"][-1] == {"role": "user", "content": "How much?"}


def test_num_ctx_is_sent_by_default(ollama_settings: Settings) -> None:
    server = Server(_stream("x"))

    _answer(_llm(ollama_settings, server))

    assert server.json()["options"]["num_ctx"] == 32768


def test_system_is_answer_prompt_citing_prompt_and_sorted_documents(ollama_settings: Settings) -> None:
    server = Server(_stream("x"))
    shuffled = (DOCUMENTS[2], DOCUMENTS[0], DOCUMENTS[1])

    _answer(_llm(ollama_settings, server, documents=shuffled))

    system = server.json()["messages"][0]
    assert system["role"] == "system"
    assert system["content"] == build_system_prompt(PROMPT, CITING, DOCUMENTS)
    text = system["content"]
    assert text.index(PROMPT.text) < text.index(CITING.text) < text.index('id="a-steps"')
    assert text.index('id="a-steps"') < text.index('id="b-fees"') < text.index('id="c-sponsor"')
    assert '<document id="b-fees" title="Title &quot;of&quot; b-fees">\nText of b-fees.\n</document>' in text


def test_system_message_is_byte_identical_between_requests(ollama_settings: Settings) -> None:
    server = Server(_stream("x"))
    llm = _llm(ollama_settings, server)

    _answer(llm, "first", ())
    _answer(llm, "second", (Exchange("q1", "a1"),))

    first, second = (r.content for r in server.requests)
    # Everything up to the first user message (model and system) is the same bytes.
    assert first[: first.index(b'"user"')] == second[: second.index(b'"user"')]
    assert server.json(0)["messages"][0] == server.json(1)["messages"][0]


def test_history_is_alternating_plain_messages() -> None:
    request = build_chat_request(
        model="m",
        num_ctx=4096,
        system="S",
        question="q3",
        history=(Exchange("q1", "a1"), Exchange("q2", "a2")),
    )

    assert request["messages"] == [
        {"role": "system", "content": "S"},
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q2"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "q3"},
    ]


def test_no_documents_is_an_error(ollama_settings: Settings) -> None:
    server = Server(_stream("x"))

    with pytest.raises(LLMError):
        _answer(_llm(ollama_settings, server, documents=()))
    assert server.requests == []


# --- markers (I/O matrix) -----------------------------------------------------------


def test_cited_answer() -> None:
    assert _parse("90 ยูโร [[udi-fees]].") == [AnswerChunk("90 ยูโร.", ("udi-fees",))]


def test_split_marker_is_never_shown_and_its_id_arrives_once() -> None:
    chunks = _parse("ข้อมูล [[", "udi-", "fees]] ต่อ")

    assert all("[" not in c.text and "]" not in c.text for c in chunks)
    assert "".join(c.text for c in chunks) == "ข้อมูล ต่อ"
    assert [sid for c in chunks for sid in c.source_ids] == ["udi-fees"]


@pytest.mark.parametrize(
    "pieces",
    [
        ["ข้อมูล [", "[udi-fees]", "] ต่อ"],
        ["ข้อมูล ", "[[udi-fees", "]]", " ต่อ"],
        list("ข้อมูล [[udi-fees]] ต่อ"),
    ],
    ids=["single-brackets", "whitespace-alone", "char-by-char"],
)
def test_marker_split_anywhere(pieces: list[str]) -> None:
    chunks = _parse(*pieces)

    assert "".join(c.text for c in chunks) == "ข้อมูล ต่อ"
    assert [sid for c in chunks for sid in c.source_ids] == ["udi-fees"]


def test_adjacent_markers() -> None:
    assert _parse("x [[a]][[b]]") == [AnswerChunk("x", ("a", "b"))]


def test_markers_separated_by_whitespace_and_on_a_new_line() -> None:
    chunks = _parse("x [[a]] [[b]]\n- y\n[[c]]\n- z")

    # Spaces before a marker are stripped; line breaks stay.
    assert "".join(c.text for c in chunks) == "x\n- y\n\n- z"
    assert [sid for c in chunks for sid in c.source_ids] == ["a", "b", "c"]


@pytest.mark.parametrize(
    "pieces",
    [["1.\n\n[[a]] 2"], ["1.\n\n", "[[a]] 2"], ["1.\n", "\n[[", "a]] 2"]],
    ids=["one-piece", "break-then-marker", "split"],
)
def test_marker_at_the_start_of_a_line_keeps_the_paragraph_break(pieces: list[str]) -> None:
    chunks = _parse(*pieces)

    assert "".join(c.text for c in chunks) == "1.\n\n 2"
    assert [sid for c in chunks for sid in c.source_ids] == ["a"]


@pytest.mark.parametrize(
    ("text", "shown"),
    [
        ("see [1] and [2]", "see [1] and [2]"),
        ("open [[ at the end", "open [[ at the end"),
        ("ends with [[", "ends with [["),
        ("ends with [[udi-f", "ends with [[udi-f"),
        ("ends with [[udi-fees]", "ends with [[udi-fees]"),
        ("blank [[ ]] body", "blank [[ ]] body"),
        ("line\n[[break\n]] here", "line\n[[break\n]] here"),
        ("single [a] bracket", "single [a] bracket"),
    ],
)
def test_not_a_marker_is_shown_as_written(text: str, shown: str) -> None:
    chunks = _parse(text)

    assert "".join(c.text for c in chunks) == shown
    assert all(c.source_ids == () for c in chunks)


def test_too_long_body_is_not_a_marker() -> None:
    long_body = "x" * (MAX_MARKER_BODY + 1)
    text = f"a [[{long_body}]] b"

    chunks = _parse(text)

    assert "".join(c.text for c in chunks) == text
    assert all(c.source_ids == () for c in chunks)


def test_longest_body_is_a_marker_and_non_kebab_ids_pass_through() -> None:
    body = "Not Kebab " + "y" * (MAX_MARKER_BODY - 10)
    assert _parse(f"a [[{body}]]") == [AnswerChunk("a", (body,))]


def test_id_is_stripped() -> None:
    assert _parse("a [[ udi-fees ]].") == [AnswerChunk("a.", ("udi-fees",))]


def test_no_empty_chunks() -> None:
    assert _parse("", "  ", "[[a]]", "") == [AnswerChunk("", ("a",))]


# --- stream -------------------------------------------------------------------------


def test_stream_yields_chunks_then_usage_last(ollama_settings: Settings) -> None:
    server = Server(_stream("90 ยูโร [[udi-fees]].", " ต่อ"))

    items = _answer(_llm(ollama_settings, server))

    assert items == [
        AnswerChunk("90 ยูโร.", ("udi-fees",)),
        AnswerChunk(" ต่อ"),
        Usage(input_tokens=1200, output_tokens=300, cache_read_tokens=0, cache_write_tokens=0),
    ]


def test_split_marker_across_stream_lines(ollama_settings: Settings) -> None:
    server = Server(_stream("ข้อมูล [[", "udi-", "fees]] ต่อ"))

    text, ids, usage = _split(_answer(_llm(ollama_settings, server)))

    assert (text, ids, len(usage)) == ("ข้อมูล ต่อ", ["udi-fees"], 1)


def test_open_marker_is_flushed_at_the_end(ollama_settings: Settings) -> None:
    server = Server(_stream("ok [[a]] and [["))

    items = _answer(_llm(ollama_settings, server))

    assert items[:-1] == [AnswerChunk("ok and", ("a",)), AnswerChunk(" [[")]
    assert isinstance(items[-1], Usage)


def test_thinking_is_ignored(ollama_settings: Settings) -> None:
    server = Server(
        _body(_thinking("secret reasoning [[x]]"), _content("A [[a]]"), _thinking("more"), _final())
    )

    text, ids, _ = _split(_answer(_llm(ollama_settings, server)))

    assert (text, ids) == ("A", ["a"])


def test_text_only_answer_has_no_ids(ollama_settings: Settings) -> None:
    text, ids, usage = _split(_answer(_llm(ollama_settings, Server(_stream("no sources here")))))

    assert (text, ids, len(usage)) == ("no sources here", [], 1)


def test_blank_lines_are_skipped(ollama_settings: Settings) -> None:
    server = Server(b"\n" + _body(_content("A")) + b"\n\n" + _body(_final()))

    text, _, usage = _split(_answer(_llm(ollama_settings, server)))

    assert (text, len(usage)) == ("A", 1)


@pytest.mark.parametrize(
    ("final", "usage"),
    [
        (_final(prompt_eval_count=None, eval_count=None), Usage(0, 0, 0, 0)),
        (_final(prompt_eval_count=None, eval_count=7), Usage(0, 7, 0, 0)),
        (_final(prompt_eval_count="12", eval_count=-1), Usage(0, 0, 0, 0)),
        (_final(prompt_eval_count=True, eval_count=3.5), Usage(0, 0, 0, 0)),
    ],
)
def test_missing_or_malformed_counts_are_zero(
    ollama_settings: Settings, final: dict[str, Any], usage: Usage
) -> None:
    items = _answer(_llm(ollama_settings, Server(_stream("A", final=final))))

    assert items[-1] == usage


# --- errors -------------------------------------------------------------------------


def _fails(settings: Settings, server: Server) -> LLMError:
    with pytest.raises(LLMError) as caught:
        _answer(_llm(settings, server))
    return caught.value


@pytest.mark.parametrize(
    "error",
    [
        httpx.ConnectError("connection refused"),
        httpx.ReadTimeout("slow"),
        httpx.RemoteProtocolError("cut"),
    ],
)
def test_transport_errors_become_llm_errors(ollama_settings: Settings, error: Exception) -> None:
    caught = _fails(ollama_settings, Server(error=error))

    assert type(caught) is LLMError
    assert type(error).__name__ in str(caught)
    assert not isinstance(caught, httpx.HTTPError)


@pytest.mark.parametrize("status", [400, 404, 500, 503])
def test_http_status_other_than_200_is_an_error_logged_by_status(
    ollama_settings: Settings, status: int, caplog: pytest.LogCaptureFixture
) -> None:
    body = _body({"error": 'model "qwen3.5:9b" not found, try pulling it first'})

    with caplog.at_level(logging.WARNING, logger="app.adapters.ollama_llm"):
        caught = _fails(ollama_settings, Server(body, status=status))

    assert str(status) in str(caught)
    assert [r.getMessage() for r in caplog.records] == [f"Ollama answered HTTP {status}"]
    assert "not found" not in caplog.text


def test_bad_json_line_is_an_error(ollama_settings: Settings) -> None:
    server = Server(_body(_content("A [[a]]"), "{not json", _final()))
    items: list[AnswerChunk | Usage] = []

    with pytest.raises(LLMError):
        for item in _llm(ollama_settings, server).answer("q", ()):
            items.append(item)

    assert items == [AnswerChunk("A", ("a",))]


@pytest.mark.parametrize("line", ['"a string"', "[1, 2]", "42"])
def test_json_that_is_not_an_object_is_an_error(ollama_settings: Settings, line: str) -> None:
    _fails(ollama_settings, Server(_body(_content("A"), line, _final())))


def test_error_field_mid_stream_is_an_error_logged_without_its_text(
    ollama_settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    server = Server(_body(_content("A"), {"error": "secret question echoed"}))

    with caplog.at_level(logging.WARNING, logger="app.adapters.ollama_llm"):
        caught = _fails(ollama_settings, server)

    assert "secret question echoed" not in str(caught)
    assert [r.getMessage() for r in caplog.records] == ["Ollama reported an error"]
    assert "secret question echoed" not in caplog.text


@pytest.mark.parametrize("reason", ["length", "load", "unload", None])
def test_done_reason_other_than_stop_is_incomplete(ollama_settings: Settings, reason: str | None) -> None:
    final = _final()
    final["done_reason"] = reason
    if reason is None:
        del final["done_reason"]

    caught = _fails(ollama_settings, Server(_stream("A [[a]] held [[", final=final)))

    assert "incomplete" in str(caught)


def test_stream_that_ends_before_done_is_incomplete(ollama_settings: Settings) -> None:
    caught = _fails(ollama_settings, Server(_body(_content("A [[a]]"))))

    assert "incomplete" in str(caught)


def test_no_usage_after_an_error(ollama_settings: Settings) -> None:
    server = Server(_body(_content("A [[a]]"), {"error": "boom"}, _final()))
    items: list[AnswerChunk | Usage] = []

    with pytest.raises(LLMError):
        for item in _llm(ollama_settings, server).answer("q", ()):
            items.append(item)

    assert not any(isinstance(i, Usage) for i in items)


def test_closing_the_stream_early_closes_the_response(ollama_settings: Settings) -> None:
    closed: list[bool] = []

    class Body(httpx.SyncByteStream):
        def __iter__(self) -> Iterator[bytes]:
            yield _body(_content("A [[a]]"))
            yield _body(_content("B"), _final())

        def close(self) -> None:
            closed.append(True)

    def server(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, stream=Body())

    stream = _llm(ollama_settings, server).answer("q", ())
    assert next(stream) == AnswerChunk("A", ("a",))
    stream.close()

    assert closed == [True]


def test_classify_and_translate_are_not_implemented(ollama_settings: Settings) -> None:
    llm = _llm(ollama_settings, Server())

    with pytest.raises(NotImplementedError):
        llm.classify("q", ())
    with pytest.raises(NotImplementedError):
        llm.translate("t")
