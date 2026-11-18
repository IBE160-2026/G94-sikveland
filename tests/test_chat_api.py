"""`POST /api/chat`: the JSON Lines stream contract (AD-8) with a scripted model."""

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.file_prompts import PromptError, load_prompt
from app.adapters.mock_llm import MODEL_NAME as MOCK_MODEL_NAME
from app.adapters.mock_llm import MockLLM
from app.adapters.ollama_llm import OllamaLLM
from app.config import ROOT, Settings
from app.main import create_app
from app.pipeline.filter import REMOVED_MARKER
from app.ports.llm import AnswerChunk, Exchange, LLMError, LLMRefusalError, Usage
from app.web.chat import FIXED_REPLY_KEYS
from tests.fakes.fake_llm import CLASSIFY_USAGE, ClassifyCall, ScriptedLLM

# S1 is linked to an item of the family checklist only; S2 to no checklist item.
S1 = "embassy-necessary-documents"
S2 = "embassy-online-registration"
S1_PURPOSES = ("family",)
QUESTION = "How much is the visa fee?"


def _client(settings: Settings, llm: Any) -> TestClient:
    return TestClient(create_app(settings, llm=llm), raise_server_exceptions=False)


def _post(client: TestClient, body: Any) -> tuple[Any, list[str]]:
    response = client.post("/api/chat", json=body)
    return response, response.text.splitlines(keepends=False)


def _events(client: TestClient, body: Any) -> list[dict[str, Any]]:
    response, lines = _post(client, body)
    assert response.status_code == 200
    assert response.text.endswith("\n")
    return [json.loads(line) for line in lines]


def _texts(settings: Settings) -> dict[str, str]:
    return {key: t.th for key, t in create_app(settings, llm=ScriptedLLM()).state.content.texts().items()}


def _source(client: TestClient, sid: str) -> dict[str, str]:
    source = client.app.state.knowledge_base.source(sid)
    return {"id": source.id, "title": source.title, "url": source.url}


def _meta(question: str = QUESTION, removed: bool = False) -> dict[str, Any]:
    return {
        "type": "meta",
        "category": "general",
        "personal_info_removed": removed,
        "clean_question": question,
    }


def _sources(*items: dict[str, str], purposes: tuple[str, ...] = ()) -> dict[str, Any]:
    return {
        "type": "sources",
        "sources": list(items),
        "checklist": bool(purposes),
        "checklist_purposes": list(purposes),
    }


ERROR = {"type": "error", "key": "error"}
DONE = {"type": "done"}


def test_cited_answer_streams_meta_text_sources_done(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A"), AnswerChunk("", (S1,)), AnswerChunk("B"), AnswerChunk("C")])
    client = _client(settings, llm)

    response, lines = _post(client, {"question": QUESTION, "history": []})

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/jsonl")
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["x-accel-buffering"] == "no"
    assert [json.loads(line) for line in lines] == [
        _meta(),
        {"type": "text", "delta": "A"},
        {"type": "text", "delta": "B"},
        {"type": "text", "delta": "C"},
        _sources(_source(client, S1), purposes=S1_PURPOSES),
        DONE,
    ]


def test_sources_in_first_cited_order_each_once(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("x", (S2,)), AnswerChunk("y", (S1, S2)), AnswerChunk("z", (S1,))])
    client = _client(settings, llm)

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(_source(client, S2), _source(client, S1), purposes=S1_PURPOSES)


def test_thai_is_sent_as_utf8_not_escaped(settings: Settings) -> None:
    thai = "ค่าธรรมเนียม"
    client = _client(settings, ScriptedLLM([AnswerChunk(thai, (S1,))]))

    _, lines = _post(client, {"question": thai, "history": []})

    assert thai in lines[0] and thai in lines[1]
    assert "\\u0e" not in "".join(lines)


def test_zero_citations_sends_the_no_answer_text(settings: Settings) -> None:
    client = _client(settings, ScriptedLLM([AnswerChunk("an uncited guess")]))

    events = _events(client, {"question": QUESTION, "history": []})

    assert events == [
        _meta(),
        {"type": "text", "delta": _texts(settings)["reply-no-answer"]},
        _sources(),
        DONE,
    ]
    assert settings.adviser_contact in events[1]["delta"]
    assert "an uncited guess" not in json.dumps(events)


def test_personal_info_is_removed_before_the_model(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])
    client = _client(settings, llm)

    events = _events(client, {"question": "passport AA1234567 which documents?", "history": []})

    clean = f"passport {REMOVED_MARKER} which documents?"
    assert llm.calls[0].question == clean
    assert events[0] == _meta(clean, removed=True)


def test_history_is_filtered_and_does_not_set_the_flag(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])
    client = _client(settings, llm)
    history = [{"question": "my ID is 1-2345-67890-12-3", "answer": "Thanks."}]

    events = _events(client, {"question": QUESTION, "history": history})

    assert llm.calls[0].history == (Exchange(f"my ID is {REMOVED_MARKER}", "Thanks."),)
    assert events[0] == _meta()


def test_question_is_stripped(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])

    events = _events(_client(settings, llm), {"question": f"  {QUESTION}\n", "history": []})

    assert llm.calls[0].question == QUESTION
    assert events[0]["clean_question"] == QUESTION


@pytest.mark.parametrize(
    "llm",
    [ScriptedLLM([], error=LLMError("boom")), ScriptedLLM([], refusal=True)],
    ids=["error", "refusal"],
)
def test_error_before_text(settings: Settings, llm: ScriptedLLM) -> None:
    assert _events(_client(settings, llm), {"question": QUESTION, "history": []}) == [_meta(), ERROR]


def test_error_before_the_first_citation_sends_no_model_text(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("held text")], error=LLMError("boom"))

    assert _events(_client(settings, llm), {"question": QUESTION, "history": []}) == [_meta(), ERROR]


def test_error_after_text_keeps_the_sent_text(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,)), AnswerChunk("B")], error=LLMError("cut"))

    events = _events(_client(settings, llm), {"question": QUESTION, "history": []})

    assert events == [
        _meta(),
        {"type": "text", "delta": "A"},
        {"type": "text", "delta": "B"},
        ERROR,
    ]


def test_unknown_cited_id_is_dropped_and_the_answer_continues(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,)), AnswerChunk("B", ("no-such-source",))])
    client = _client(settings, llm)

    events = _events(client, {"question": QUESTION, "history": []})

    assert events == [
        _meta(),
        {"type": "text", "delta": "A"},
        {"type": "text", "delta": "B"},
        _sources(_source(client, S1), purposes=S1_PURPOSES),
        DONE,
    ]
    assert "no-such-source" not in json.dumps(events)
    [line] = _log(settings)
    assert (line["outcome"], line["unknown_source_ids"]) == ("answered", 1)


def test_only_unknown_cited_ids_send_the_no_answer_text(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("a guess", ("no-such-source",))])

    events = _events(_client(settings, llm), {"question": QUESTION, "history": []})

    assert events == [
        _meta(),
        {"type": "text", "delta": _texts(settings)["reply-no-answer"]},
        _sources(),
        DONE,
    ]
    [line] = _log(settings)
    assert (line["outcome"], line["unknown_source_ids"]) == ("no_answer", 1)


class _Exploding(ScriptedLLM):
    """Fails with an exception that is not an `LLMError`, after some cited text."""

    def _stream(self) -> Iterator[AnswerChunk | Usage]:
        yield AnswerChunk("A", (S1,))
        raise RuntimeError("secret question text")


def test_unexpected_exception_becomes_an_error_event_logged_by_class_only(
    settings: Settings, caplog: pytest.LogCaptureFixture
) -> None:
    question = "my private question"
    with caplog.at_level(logging.DEBUG):
        events = _events(_client(settings, _Exploding()), {"question": question, "history": []})

    assert events == [_meta(question), {"type": "text", "delta": "A"}, ERROR]
    assert "RuntimeError" in caplog.text
    assert "secret question text" not in caplog.text
    assert question not in caplog.text


def test_no_question_or_answer_text_in_logs(settings: Settings, caplog: pytest.LogCaptureFixture) -> None:
    llm = ScriptedLLM([AnswerChunk("the answer text", (S1,))], error=LLMError("boom"))
    with caplog.at_level(logging.DEBUG):
        _events(_client(settings, llm), {"question": "the question text", "history": []})

    assert "the question text" not in caplog.text
    assert "the answer text" not in caplog.text


def test_without_a_key_the_real_adapter_fails_as_an_error_event(settings: Settings) -> None:
    created = create_app(settings)
    assert isinstance(created.state.llm, AnthropicLLM)

    client = TestClient(created)
    events = _events(client, {"question": QUESTION, "history": []})

    # The classify call fails first, so nothing is categorised or answered.
    assert events == [ERROR]
    [line] = _log(settings)
    assert (line["outcome"], line["category"], line["cost_usd"]) == ("error", None, None)


def test_broken_prompt_file_stops_startup(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt = tmp_path / "answer-system.md"
    prompt.write_text("no version line\ntext\n", encoding="utf-8")
    monkeypatch.setattr(app.main, "ANSWER_PROMPT_FILE", prompt)

    with pytest.raises(PromptError):
        create_app(settings, llm=ScriptedLLM())


def test_answer_prompt_is_kept_for_the_request_log(settings: Settings) -> None:
    assert create_app(settings, llm=ScriptedLLM()).state.answer_prompt.version == "1"


@pytest.mark.parametrize(
    "body",
    [
        {"question": "", "history": []},
        {"question": "   \n\t ", "history": []},
        {"question": "x" * 1001, "history": []},
        {"question": QUESTION, "history": [{"question": "q", "answer": "a"}] * 11},
        {"question": 5, "history": []},
        {"question": None, "history": []},
        {"question": QUESTION, "history": "none"},
        {"question": QUESTION, "history": [{"question": "q"}]},
        {"question": QUESTION, "history": [{"question": "q", "answer": 1}]},
        {"question": QUESTION, "history": [{"question": "q", "answer": "a", "extra": 1}]},
        {"question": QUESTION, "history": [], "extra": True},
        {"question": QUESTION, "history": [{"question": "", "answer": "a"}]},
        {"question": QUESTION, "history": [{"question": "  \n", "answer": "a"}]},
        {"question": QUESTION, "history": [{"question": "q", "answer": ""}]},
        {"question": QUESTION, "history": [{"question": "q", "answer": " \t "}]},
        {"question": QUESTION, "history": [{"question": "q", "answer": "a" * 10001}]},
        {"question": QUESTION, "history": [{"question": "q" * 1001, "answer": "a"}]},
        {"history": []},
        [QUESTION],
        "just a string",
    ],
    ids=[
        "empty",
        "whitespace",
        "too-long",
        "history-too-long",
        "question-int",
        "question-null",
        "history-not-list",
        "history-missing-answer",
        "history-answer-int",
        "history-extra-field",
        "extra-field",
        "history-empty-question",
        "history-whitespace-question",
        "history-empty-answer",
        "history-whitespace-answer",
        "history-answer-too-long",
        "history-question-too-long",
        "no-question",
        "body-list",
        "body-string",
    ],
)
def test_bad_request_is_422_and_never_calls_the_model(settings: Settings, body: Any) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])

    response = _client(settings, llm).post("/api/chat", json=body)

    assert response.status_code == 422
    error = response.json()["error"]
    assert set(response.json()) == {"error"}
    assert error["code"] == "invalid_request"
    assert isinstance(error["message"], str) and error["message"]
    assert llm.calls == []


def test_invalid_json_is_422(settings: Settings) -> None:
    llm = ScriptedLLM()
    response = _client(settings, llm).post(
        "/api/chat", content=b"{not json", headers={"content-type": "application/json"}
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "invalid_request"
    assert llm.calls == []


def test_422_message_does_not_echo_the_question(settings: Settings) -> None:
    question = "passport AA1234567 " + "x" * 1000

    response = _client(settings, ScriptedLLM()).post("/api/chat", json={"question": question})

    assert response.status_code == 422
    assert "AA1234567" not in response.text


def test_extra_key_is_not_echoed_in_the_422(settings: Settings) -> None:
    llm = ScriptedLLM()
    body = {
        "question": "x",
        "passport AA1234567": 1,
        "history": [{"question": "q", "answer": "a", "ID 1234567890123": 1}],
    }

    response = _client(settings, llm).post("/api/chat", json=body)

    assert response.status_code == 422
    assert "AA1234567" not in response.text
    assert "1234567890123" not in response.text
    assert "unknown field" in response.json()["error"]["message"]
    assert llm.calls == []


def test_limits_are_inclusive(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])
    turn = {"question": "q" * 1000, "answer": "a" * 10000}
    body = {"question": "x" * 1000, "history": [turn] * 10}

    events = _events(_client(settings, llm), body)

    assert events[-1] == DONE
    assert len(llm.calls[0].history) == 10


def test_follow_up_sends_the_history_to_the_model_in_order(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])
    client = _client(settings, llm)
    history = [
        {"question": "first question", "answer": "first answer"},
        {"question": "passport AA1234567, second question", "answer": "ID 1234567890123 noted"},
    ]

    events = _events(client, {"question": "and the fee?", "history": history})

    assert llm.calls[0].question == "and the fee?"
    assert llm.calls[0].history == (
        Exchange("first question", "first answer"),
        Exchange(f"passport {REMOVED_MARKER}, second question", f"ID {REMOVED_MARKER} noted"),
    )
    # Only the new question sets the flag; it had no personal information.
    assert events[0]["personal_info_removed"] is False
    assert events[-1] == {"type": "done"}


# --- Request log (Story 1.8) ---------------------------------------------------------

LOG_FIELDS = {
    "timestamp",
    "endpoint",
    "outcome",
    "category",
    "prompt_versions",
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "classify_input_tokens",
    "classify_output_tokens",
    "cost_usd",
    "unknown_source_ids",
}
# (400 x 0.10 + 20 x 0.50) / 1e6 with the default PRICE_SMALL_* prices
CLASSIFY_COST = 0.00005
SPEC_USAGE = Usage(input_tokens=1000, output_tokens=200, cache_read_tokens=50000, cache_write_tokens=0)


def _log(settings: Settings) -> list[dict[str, Any]]:
    path = Path(settings.request_log_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_cited_answer_logs_one_line_with_tokens_and_cost(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))], usage=SPEC_USAGE)
    client = _client(settings, llm)

    _events(client, {"question": QUESTION, "history": []})

    [line] = _log(settings)
    assert set(line) == LOG_FIELDS
    assert re.fullmatch(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z", line["timestamp"])
    assert {k: v for k, v in line.items() if k != "timestamp"} == {
        "endpoint": "chat",
        "outcome": "answered",
        "category": "general",
        "prompt_versions": {
            "answer": client.app.state.answer_prompt.version,
            "classifier": client.app.state.classifier_prompt.version,
        },
        "model": settings.model_answer,
        "input_tokens": 1000,
        "output_tokens": 200,
        "cache_read_tokens": 50000,
        "cache_write_tokens": 0,
        "classify_input_tokens": CLASSIFY_USAGE.input_tokens,
        "classify_output_tokens": CLASSIFY_USAGE.output_tokens,
        # (1000x4 + 200x20 + 50000x0.2 + 0x5) / 1e6 with the default prices, plus the classify call
        "cost_usd": 0.018 + CLASSIFY_COST,
        "unknown_source_ids": 0,
    }


def test_no_answer_logs_no_answer_with_tokens_and_cost(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("uncited")], usage=SPEC_USAGE)

    _events(_client(settings, llm), {"question": QUESTION, "history": []})

    [line] = _log(settings)
    assert line["outcome"] == "no_answer"
    assert (line["input_tokens"], line["cost_usd"]) == (1000, 0.018 + CLASSIFY_COST)


@pytest.mark.parametrize(
    "llm",
    [
        ScriptedLLM([], error=LLMError("boom")),
        ScriptedLLM([AnswerChunk("A", (S1,))], error=LLMError("cut")),
        ScriptedLLM([], refusal=True),
        _Exploding(),
    ],
    ids=["error-before-text", "error-after-text", "refusal", "unexpected"],
)
def test_answer_error_logs_null_answer_tokens_and_the_classify_cost(
    settings: Settings, llm: ScriptedLLM
) -> None:
    events = _events(_client(settings, llm), {"question": QUESTION, "history": []})

    assert events[-1] == ERROR
    [line] = _log(settings)
    assert set(line) == LOG_FIELDS
    assert line["outcome"] == "error"
    assert line["category"] == "general"
    for field in (
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        # The stream ended before the sources were known.
        "unknown_source_ids",
    ):
        assert line[field] is None, field
    # The classify call ran and is paid for.
    assert line["classify_input_tokens"] == CLASSIFY_USAGE.input_tokens
    assert line["cost_usd"] == CLASSIFY_COST


def test_client_gone_mid_answer_logs_incomplete(settings: Settings) -> None:
    from app.pipeline.answer import answer_question
    from app.web.chat import _lines

    logged: list[tuple[Any, ...]] = []
    llm = ScriptedLLM([AnswerChunk("A", (S1,)), AnswerChunk("B"), AnswerChunk("C")], usage=SPEC_USAGE)
    kb = create_app(settings, llm=llm).state.knowledge_base
    events = answer_question(QUESTION, (), llm, kb, "no answer", fixed_replies={})
    lines = _lines(events, lambda *args: logged.append(args), {})

    assert json.loads(next(lines))["type"] == "meta"
    assert json.loads(next(lines)) == {"type": "text", "delta": "A"}
    assert logged == []
    # Simulates the close that garbage collection performs on the abandoned stream
    # when the client goes away (Starlette does not close it itself).
    lines.close()

    assert logged == [("incomplete", "general", None, CLASSIFY_USAGE, None)]
    assert events.gi_frame is None  # the pipeline (and the model stream) is closed too


def test_client_gone_during_a_fixed_reply_still_logs_the_classify_cost(settings: Settings) -> None:
    from app.pipeline.answer import answer_question
    from app.web.chat import _lines
    from app.web.request_log import answer_prices, request_line, small_prices

    logged: list[dict[str, Any]] = []

    def log(outcome: Any, category: Any, usage: Any, classify_usage: Any, unknown: Any) -> None:
        logged.append(
            request_line(
                endpoint="chat",
                outcome=outcome,
                category=category,
                prompt_versions={},
                model=settings.model_answer,
                usage=usage,
                prices=answer_prices(settings),
                classify_usage=classify_usage,
                classify_prices=small_prices(settings),
                unknown_source_ids=unknown,
            )
        )

    llm = ScriptedLLM(category="individual_assessment")
    kb = create_app(settings, llm=llm).state.knowledge_base
    fixed = {"individual_assessment": "only the embassy decides"}
    events = answer_question("จะได้วีซ่าไหม", (), llm, kb, "no answer", fixed_replies=fixed)
    lines = _lines(events, log, {})

    assert json.loads(next(lines))["category"] == "individual_assessment"
    lines.close()  # the client went away after `meta`

    [line] = logged
    assert (line["outcome"], line["category"]) == ("incomplete", "individual_assessment")
    for field in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"):
        assert line[field] is None, field
    assert (line["classify_input_tokens"], line["classify_output_tokens"]) == (400, 20)
    assert line["cost_usd"] == CLASSIFY_COST
    assert llm.calls == []


def test_privacy_no_question_answer_or_personal_info_in_the_log(settings: Settings) -> None:
    answer = "the answer text about the fee"
    client = _client(settings, ScriptedLLM([AnswerChunk(answer, (S1,))], usage=SPEC_USAGE))
    question = "passport AA1234567 how much is the fee?"

    history = [{"question": "earlier q", "answer": "earlier a"}]

    events = _events(client, {"question": question, "history": history})

    assert events[0]["personal_info_removed"] is True
    raw = Path(settings.request_log_path).read_text(encoding="utf-8")
    assert len(raw.splitlines()) == 1
    for secret in (
        question,
        "AA1234567",
        REMOVED_MARKER,
        "how much is the fee",
        answer,
        "earlier q",
        "earlier a",
        _source(client, S1)["title"],
        S1,
        "personal_info_removed",
    ):
        assert secret not in raw


def test_unwritable_log_does_not_break_the_answer(
    settings: Settings, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    blocker = tmp_path / "a-file"
    blocker.write_text("x", encoding="utf-8")
    broken = settings.model_copy(update={"request_log_path": str(blocker / "logs" / "requests.jsonl")})
    client = _client(broken, ScriptedLLM([AnswerChunk("A", (S1,))]))

    with caplog.at_level(logging.WARNING):
        first = _events(client, {"question": QUESTION, "history": []})
        second = _events(client, {"question": QUESTION, "history": []})

    assert (
        first
        == second
        == [
            _meta(),
            {"type": "text", "delta": "A"},
            _sources(_source(client, S1), purposes=S1_PURPOSES),
            DONE,
        ]
    )
    warnings = [r.getMessage() for r in caplog.records if "request log" in r.getMessage()]
    assert len(warnings) == 1
    assert re.fullmatch(r"request log not written: \w+Error", warnings[0])


def test_bad_request_writes_no_line(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])

    response = _client(settings, llm).post("/api/chat", json={"question": ""})

    assert response.status_code == 422
    assert not Path(settings.request_log_path).exists()


def test_one_line_per_request(settings: Settings) -> None:
    client = _client(settings, ScriptedLLM([AnswerChunk("A", (S1,))]))

    for _ in range(3):
        _events(client, {"question": QUESTION, "history": []})

    assert [line["outcome"] for line in _log(settings)] == ["answered"] * 3


def test_relative_log_path_is_resolved_against_the_project_root(settings: Settings) -> None:
    relative = settings.model_copy(update={"request_log_path": "data/requests.jsonl"})

    created = create_app(relative, llm=ScriptedLLM())

    assert created.state.request_log.path == ROOT / "data" / "requests.jsonl"


def test_absolute_log_path_is_kept(settings: Settings) -> None:
    created = create_app(settings, llm=ScriptedLLM())

    assert created.state.request_log.path == Path(settings.request_log_path)


# --- Provider choice: Ollama ---------------------------------------------------------


def _ollama(settings: Settings) -> Settings:
    return settings.model_copy(update={"llm_provider": "ollama", "ollama_model": "qwen-test:1b"})


def _ollama_classified(category: str = "general") -> bytes:
    reply = {
        "message": {"role": "assistant", "content": json.dumps({"category": category})},
        "done": True,
        "done_reason": "stop",
        "prompt_eval_count": 350,
        "eval_count": 9,
    }
    return json.dumps(reply).encode()


def _ollama_handler(
    body: bytes, requests: list[httpx.Request] | None = None, category: str = "general"
) -> Any:
    """Answers the classify call (not streamed) with `category`, the answer call with `body`."""

    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
        if json.loads(request.content)["stream"] is False:
            return httpx.Response(200, content=_ollama_classified(category))
        return httpx.Response(200, content=body)

    return handler


def _ollama_llm(
    settings: Settings, body: bytes, requests: list[httpx.Request] | None = None, category: str = "general"
) -> OllamaLLM:
    return OllamaLLM(
        settings,
        load_knowledge_base(app.main.KNOWLEDGE_BASE_DIR),
        load_prompt(app.main.ANSWER_PROMPT_FILE),
        load_prompt(app.main.CITING_PROMPT_FILE),
        load_prompt(app.main.CLASSIFIER_PROMPT_FILE),
        load_prompt(app.main.TRANSLATE_PROMPT_FILE),
        client=httpx.Client(transport=httpx.MockTransport(_ollama_handler(body, requests, category))),
    )


def _ollama_stream(*pieces: str) -> bytes:
    lines: list[dict[str, Any]] = [{"message": {"role": "assistant", "thinking": "hmm"}, "done": False}]
    lines += [{"message": {"role": "assistant", "content": p}, "done": False} for p in pieces]
    lines.append(
        {
            "message": {"role": "assistant", "content": ""},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 24600,
            "eval_count": 900,
        }
    )
    return "".join(json.dumps(line, ensure_ascii=False) + "\n" for line in lines).encode()


def test_default_provider_is_anthropic(settings: Settings) -> None:
    created = create_app(settings)

    assert settings.llm_provider == "anthropic"
    assert isinstance(created.state.llm, AnthropicLLM)
    assert created.state.prompt_versions == {
        "answer": created.state.answer_prompt.version,
        "classifier": created.state.classifier_prompt.version,
    }


def test_ollama_provider_wires_the_ollama_adapter(settings: Settings) -> None:
    ollama = _ollama(settings)

    created = create_app(ollama)

    assert isinstance(created.state.llm, OllamaLLM)
    assert created.state.answer_model == "qwen-test:1b"
    assert created.state.no_answer_key == "reply-no-answer"
    assert created.state.fallback_usage is None
    assert created.state.prompt_versions == {
        "answer": created.state.answer_prompt.version,
        "classifier": created.state.classifier_prompt.version,
        "citing": load_prompt(app.main.CITING_PROMPT_FILE).version,
    }


def test_wired_ollama_adapter_classifies_then_answers_with_all_three_prompts(settings: Settings) -> None:
    created = create_app(_ollama(settings))
    requests: list[httpx.Request] = []
    handler = _ollama_handler(_ollama_stream("A [[udi-fees]]."), requests)
    created.state.llm._client = httpx.Client(transport=httpx.MockTransport(handler))

    _events(TestClient(created), {"question": "Fee & form <now>?", "history": []})

    classify, request = requests
    classify_messages = json.loads(classify.content)["messages"]
    assert classify_messages == [
        {"role": "system", "content": load_prompt(app.main.CLASSIFIER_PROMPT_FILE).text},
        # The tagged question, escaped so it cannot close the tag.
        {"role": "user", "content": "<question>Fee &amp; form &lt;now&gt;?</question>"},
    ]
    system = json.loads(request.content)["messages"][0]
    assert system["role"] == "system"
    content = system["content"]
    answer_text = load_prompt(app.main.ANSWER_PROMPT_FILE).text
    citing_text = load_prompt(app.main.CITING_PROMPT_FILE).text
    assert answer_text in content
    assert citing_text in content
    assert content.index(answer_text) < content.index(citing_text) < content.index("<document id=")


def test_demo_mode_wins_over_the_ollama_provider(settings: Settings) -> None:
    created = create_app(_ollama(settings).model_copy(update={"mock_llm": True}))

    assert isinstance(created.state.llm, MockLLM)
    assert created.state.answer_model == MOCK_MODEL_NAME
    assert created.state.prompt_versions == {
        "answer": created.state.answer_prompt.version,
        "classifier": created.state.classifier_prompt.version,
    }


def test_ollama_answer_streams_without_markers_and_logs_no_cost(settings: Settings) -> None:
    ollama = _ollama(settings)
    requests: list[httpx.Request] = []
    answer = "ค่าธรรมเนียม 90 ยูโร [[udi-fees]] ชำระออนไลน์ [["
    body = _ollama_stream(answer[:20], answer[20:28], answer[28:] + "embassy-online-registration]].")
    client = _client(ollama, _ollama_llm(ollama, body, requests))

    events = _events(client, {"question": "ค่าวีซ่าเท่าไหร่", "history": []})

    text = "".join(e["delta"] for e in events if e["type"] == "text")
    assert text == "ค่าธรรมเนียม 90 ยูโร ชำระออนไลน์."
    assert not any("[" in e["delta"] or "]" in e["delta"] for e in events if e["type"] == "text")
    assert events[-2] == _sources(_source(client, "udi-fees"), _source(client, S2))
    assert events[-1] == DONE
    assert [json.loads(r.content)["model"] for r in requests] == ["qwen-test:1b"] * 2

    [line] = _log(ollama)
    assert {k: v for k, v in line.items() if k != "timestamp"} == {
        "endpoint": "chat",
        "outcome": "answered",
        "category": "general",
        "prompt_versions": client.app.state.prompt_versions,
        "model": "qwen-test:1b",
        "input_tokens": 24600,
        "output_tokens": 900,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "classify_input_tokens": 350,
        "classify_output_tokens": 9,
        "cost_usd": 0.0,
        "unknown_source_ids": 0,
    }
    raw = Path(ollama.request_log_path).read_text(encoding="utf-8")
    for secret in ("ค่าวีซ่าเท่าไหร่", "ค่าธรรมเนียม", "udi-fees", "hmm"):
        assert secret not in raw


def test_ollama_unknown_marker_is_dropped_and_counted(settings: Settings) -> None:
    ollama = _ollama(settings)
    body = _ollama_stream("A [[udi-fees]] B [[made-up-id]].")
    client = _client(ollama, _ollama_llm(ollama, body))

    events = _events(client, {"question": QUESTION, "history": []})

    assert "".join(e["delta"] for e in events if e["type"] == "text") == "A B."
    assert events[-2] == _sources(_source(client, "udi-fees"))
    [line] = _log(ollama)
    assert (line["outcome"], line["unknown_source_ids"]) == ("answered", 1)


def test_ollama_answer_without_markers_sends_the_no_answer_text(settings: Settings) -> None:
    ollama = _ollama(settings)
    client = _client(ollama, _ollama_llm(ollama, _ollama_stream("ไม่ทราบ")))

    events = _events(client, {"question": QUESTION, "history": []})

    assert events == [_meta(), {"type": "text", "delta": _texts(ollama)["reply-no-answer"]}, _sources(), DONE]


def test_ollama_down_shows_the_error_text(settings: Settings) -> None:
    ollama = _ollama(settings)

    def refused(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    llm = OllamaLLM(
        ollama,
        load_knowledge_base(app.main.KNOWLEDGE_BASE_DIR),
        load_prompt(app.main.ANSWER_PROMPT_FILE),
        load_prompt(app.main.CITING_PROMPT_FILE),
        load_prompt(app.main.CLASSIFIER_PROMPT_FILE),
        load_prompt(app.main.TRANSLATE_PROMPT_FILE),
        client=httpx.Client(transport=httpx.MockTransport(refused)),
    )

    events = _events(_client(ollama, llm), {"question": QUESTION, "history": []})

    # The classify call is the first to fail.
    assert events == [ERROR]
    [line] = _log(ollama)
    assert (line["outcome"], line["category"], line["model"], line["cost_usd"]) == (
        "error",
        None,
        "qwen-test:1b",
        None,
    )


def test_broken_citing_prompt_stops_startup_only_with_ollama(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app.main, "CITING_PROMPT_FILE", tmp_path / "missing.md")

    create_app(settings, llm=ScriptedLLM())  # Claude never reads it
    with pytest.raises(PromptError):
        create_app(_ollama(settings), llm=ScriptedLLM())


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("general", "general"),
        ("individual_assessment", "individual_assessment"),
        ("out_of_scope", "out_of_scope"),
        ("reach_person", "reach_person"),
        ("done", "done"),
    ],
)
def test_ollama_classifies_and_routes(settings: Settings, category: str, expected: str) -> None:
    ollama = _ollama(settings)
    requests: list[httpx.Request] = []
    body = _ollama_stream("A [[udi-fees]].")
    client = _client(ollama, _ollama_llm(ollama, body, requests, category=category))

    events = _events(client, {"question": QUESTION, "history": [{"question": "q0", "answer": "a0"}]})

    assert events[0]["category"] == expected
    classify = json.loads(requests[0].content)
    assert (classify["stream"], classify["think"], classify["options"]) == (
        False,
        False,
        {"num_ctx": ollama.ollama_num_ctx},
    )
    assert classify["format"]["properties"]["category"]["enum"] == [
        "general",
        "individual_assessment",
        "out_of_scope",
        "reach_person",
        "done",
    ]
    if category != "general":
        assert len(requests) == 1  # no answer call
        assert events[1:] == [
            {"type": "text", "delta": _texts(ollama)[FIXED_REPLY_KEYS[category]]},
            _sources(),
            DONE,
        ]
    else:
        assert len(requests) == 2


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(404, content=b'{"error": "model not found"}'),
        httpx.Response(200, content=b"{not json"),
        httpx.Response(
            200,
            content=b'{"message": {"content": "{\\"category\\": \\"weather\\"}"}, '
            b'"done": true, "done_reason": "stop"}',
        ),
    ],
    ids=["status", "bad-json", "unknown-category"],
)
def test_ollama_classify_failure_is_an_error_event(settings: Settings, reply: httpx.Response) -> None:
    ollama = _ollama(settings)
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return reply

    llm = OllamaLLM(
        ollama,
        load_knowledge_base(app.main.KNOWLEDGE_BASE_DIR),
        load_prompt(app.main.ANSWER_PROMPT_FILE),
        load_prompt(app.main.CITING_PROMPT_FILE),
        load_prompt(app.main.CLASSIFIER_PROMPT_FILE),
        load_prompt(app.main.TRANSLATE_PROMPT_FILE),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )

    events = _events(_client(ollama, llm), {"question": QUESTION, "history": []})

    assert events == [ERROR]
    assert len(requests) == 1  # never answered


# --- Classify and route (Story 2.1) ------------------------------------------------------

OWN_CHANCES = "จะได้วีซ่าไหม"


def test_individual_assessment_gets_the_embassy_decides_text_and_no_answer_call(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("a guess", (S1,))], category="individual_assessment")
    client = _client(settings, llm)

    events = _events(client, {"question": OWN_CHANCES, "history": []})

    assert events == [
        {
            "type": "meta",
            "category": "individual_assessment",
            "personal_info_removed": False,
            "clean_question": OWN_CHANCES,
        },
        {"type": "text", "delta": _texts(settings)["reply-embassy-decides"]},
        _sources(),
        DONE,
    ]
    assert llm.calls == []  # the answer model is never called
    assert len(llm.classify_calls) == 1


@pytest.mark.parametrize(
    ("category", "question", "key"),
    [
        ("out_of_scope", "ขอวีซ่าทำงานที่นอร์เวย์ต้องทำอย่างไร", "reply-out-of-scope"),
        ("reach_person", "ขอคุยกับเจ้าหน้าที่ได้ไหม", "reply-reach-person"),
    ],
)
def test_out_of_scope_and_reach_person_get_their_fixed_text_with_the_contact(
    settings: Settings, category: str, question: str, key: str
) -> None:
    custom = settings.model_copy(update={"adviser_contact": "adviser@example.org"})
    llm = ScriptedLLM([AnswerChunk("a guess", (S1,))], category=category)
    client = _client(custom, llm)

    events = _events(client, {"question": question, "history": []})

    text = _texts(custom)[key]
    assert "adviser@example.org" in text
    assert events == [
        {"type": "meta", "category": category, "personal_info_removed": False, "clean_question": question},
        {"type": "text", "delta": text},
        _sources(),
        DONE,
    ]
    assert llm.calls == []  # the answer model is never called
    [line] = _log(custom)
    assert (line["outcome"], line["category"]) == ("fixed_reply", category)
    assert line["input_tokens"] is None


def test_every_fixed_reply_category_has_its_own_text() -> None:
    assert FIXED_REPLY_KEYS == {
        "individual_assessment": "reply-embassy-decides",
        "out_of_scope": "reply-out-of-scope",
        "reach_person": "reply-reach-person",
        "done": "feedback-question",
    }


def test_individual_assessment_log_line(settings: Settings) -> None:
    client = _client(settings, ScriptedLLM(category="individual_assessment"))

    _events(client, {"question": OWN_CHANCES, "history": []})

    [line] = _log(settings)
    assert set(line) == LOG_FIELDS
    assert line["outcome"] == "fixed_reply"
    assert line["category"] == "individual_assessment"
    for field in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens"):
        assert line[field] is None, field
    assert (line["classify_input_tokens"], line["classify_output_tokens"]) == (400, 20)
    assert line["cost_usd"] == CLASSIFY_COST
    assert line["unknown_source_ids"] == 0
    assert line["prompt_versions"]["classifier"] == client.app.state.classifier_prompt.version


def test_follow_up_is_classified_with_the_last_two_cleaned_exchanges(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (S1,))])
    history = [
        {"question": "first question", "answer": "first answer"},
        {"question": "which documents? passport AA1234567", "answer": "These documents."},
        {"question": "and the form?", "answer": "This form."},
    ]

    events = _events(_client(settings, llm), {"question": "and the fee?", "history": history})

    assert llm.classify_calls == [
        ClassifyCall(
            "and the fee?",
            (
                Exchange(f"which documents? passport {REMOVED_MARKER}", "These documents."),
                Exchange("and the form?", "This form."),
            ),
        )
    ]
    assert events[0]["category"] == "general"
    assert events[-1] == DONE


def test_classifier_sees_only_the_cleaned_question(settings: Settings) -> None:
    llm = ScriptedLLM(category="individual_assessment")

    events = _events(_client(settings, llm), {"question": "passport AA1234567 will I get it?", "history": []})

    clean = f"passport {REMOVED_MARKER} will I get it?"
    assert llm.classify_calls[0].question == clean
    assert events[0]["personal_info_removed"] is True


@pytest.mark.parametrize("question", ["ขอบคุณค่ะ", "ขอบคุณค่ะ 🙏", "Thanks!", "ok."])
def test_done_signal_gets_the_feedback_question_without_sources(settings: Settings, question: str) -> None:
    llm = ScriptedLLM([AnswerChunk("a reply", (S1,))], category="done")
    client = _client(settings, llm)

    events = _events(client, {"question": question, "history": [{"question": "q0", "answer": "a0"}]})

    assert events == [
        {"type": "meta", "category": "done", "personal_info_removed": False, "clean_question": question},
        {"type": "text", "delta": _texts(settings)["feedback-question"]},
        _sources(),
        DONE,
    ]
    assert llm.calls == []  # the answer model is never called
    [line] = _log(settings)
    assert (line["outcome"], line["category"]) == ("fixed_reply", "done")
    assert line["input_tokens"] is None


@pytest.mark.parametrize(
    "llm",
    [
        ScriptedLLM([AnswerChunk("A", (S1,))], classify_error=LLMError("boom")),
        ScriptedLLM([AnswerChunk("A", (S1,))], classify_error=LLMRefusalError("no")),
        ScriptedLLM([AnswerChunk("A", (S1,))], category="weather"),
    ],
    ids=["error", "refusal", "unknown-category"],
)
def test_classify_failure_sends_only_the_error_event(settings: Settings, llm: ScriptedLLM) -> None:
    events = _events(_client(settings, llm), {"question": QUESTION, "history": []})

    assert events == [ERROR]
    assert llm.calls == []
    [line] = _log(settings)
    assert (line["outcome"], line["category"]) == ("error", None)
    assert line["input_tokens"] is None
    if llm.classify_error is None:
        # The unknown category came from a call that ran and is paid for.
        assert line["cost_usd"] == CLASSIFY_COST
    else:
        assert line["cost_usd"] is None


def test_broken_classifier_prompt_stops_startup(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt = tmp_path / "classifier-system.md"
    prompt.write_text("no version line\ntext\n", encoding="utf-8")
    monkeypatch.setattr(app.main, "CLASSIFIER_PROMPT_FILE", prompt)

    with pytest.raises(PromptError):
        create_app(settings, llm=ScriptedLLM())


@pytest.mark.parametrize("mode", ["anthropic", "ollama", "demo"])
def test_missing_classifier_prompt_stops_startup_in_every_mode(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mode: str
) -> None:
    monkeypatch.setattr(app.main, "CLASSIFIER_PROMPT_FILE", tmp_path / "missing.md")
    update = {"anthropic": {}, "ollama": {"llm_provider": "ollama"}, "demo": {"mock_llm": True}}[mode]

    with pytest.raises(PromptError):
        create_app(settings.model_copy(update=update))


def test_classifier_prompt_is_loaded_and_versioned(settings: Settings) -> None:
    created = create_app(settings, llm=ScriptedLLM())

    assert created.state.classifier_prompt.version == "4"
    assert created.state.prompt_versions["classifier"] == "4"


def test_classify_is_priced_with_the_small_prices_only_with_claude(settings: Settings) -> None:
    from app.web.request_log import small_prices

    assert create_app(settings, llm=ScriptedLLM()).state.classify_prices == small_prices(settings)
    for update in ({"llm_provider": "ollama"}, {"mock_llm": True}):
        prices = create_app(settings.model_copy(update=update), llm=ScriptedLLM()).state.classify_prices
        assert (prices.input, prices.output, prices.cache_read, prices.cache_write) == (0, 0, 0, 0)


# --- Open the checklist from the chat (Story 3.3) ----------------------------------------
# The committed checklists (content/checklists.yaml) decide the purposes.

SPONSOR_FORM = "udi-sponsorship-form"  # items in the family and friends checklists
EMBASSY_CHECKLIST = "embassy-visitor-visa-checklist"  # items in all three checklists
FEES = "udi-fees"  # no checklist item


@pytest.mark.parametrize(
    ("cited", "purposes"),
    [
        ((SPONSOR_FORM,), ("family", "friends")),
        ((S1,), ("family",)),
        ((EMBASSY_CHECKLIST,), ("tourism", "family", "friends")),
        ((FEES,), ()),
        ((FEES, S2), ()),
        # In VISIT_PURPOSES order and each once, whatever the citation order.
        ((SPONSOR_FORM, S1, FEES), ("family", "friends")),
        ((FEES, SPONSOR_FORM, EMBASSY_CHECKLIST), ("tourism", "family", "friends")),
    ],
    ids=["family-sources", "one-purpose", "general-source", "no-link", "no-link-two", "repeats", "order"],
)
def test_sources_event_names_the_checklists_of_the_cited_sources(
    settings: Settings, cited: tuple[str, ...], purposes: tuple[str, ...]
) -> None:
    llm = ScriptedLLM([AnswerChunk("A", cited)])
    client = _client(settings, llm)

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(*(_source(client, sid) for sid in cited), purposes=purposes)
    assert events[-1] == DONE
    # One classify and one answer call only; no model call decides the button.
    assert len(llm.classify_calls) == 1
    assert len(llm.calls) == 1


def test_unknown_cited_id_counts_for_no_checklist(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", (FEES,)), AnswerChunk("B", ("no-such-source",))])
    client = _client(settings, llm)

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(_source(client, FEES))


def test_only_unknown_cited_ids_give_no_checklist(settings: Settings) -> None:
    events = _events(
        _client(settings, ScriptedLLM([AnswerChunk("x", ("no-such-source",))])), {"question": QUESTION}
    )

    assert events[-2] == _sources()


def test_one_tourism_purpose_comes_through_the_route(settings: Settings) -> None:
    # No committed source is linked to tourism items only, so the map is replaced here.
    client = _client(settings, ScriptedLLM([AnswerChunk("A", (FEES,))]))
    client.app.state.checklist_purposes = {FEES: ("tourism",)}

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(_source(client, FEES), purposes=("tourism",))


def test_a_fixed_reply_never_links_a_checklist_even_with_linked_sources() -> None:
    from app.pipeline.answer import Done, Meta, SourceRef, Sources, TextDelta
    from app.web.chat import _lines

    ref = SourceRef(SPONSOR_FORM, "t", "https://example.org/form")
    by_source = {SPONSOR_FORM: ("family", "friends")}

    def sources_event(category: str) -> dict[str, Any]:
        events = iter([Meta(category, False, "q"), TextDelta("x"), Sources((ref,)), Done()])
        return json.loads(list(_lines(events, lambda *args: None, by_source))[2])

    assert sources_event("general")["checklist_purposes"] == ["family", "friends"]
    for category in FIXED_REPLY_KEYS:
        event = sources_event(category)
        assert (event["checklist"], event["checklist_purposes"]) == (False, []), category


def test_purposes_by_source_keeps_the_purpose_order_and_each_once() -> None:
    from app.ports.content import ChecklistItem
    from app.web.chat import checklist_purposes, checklist_purposes_by_source

    def item(item_id: str, source_id: str) -> ChecklistItem:
        return ChecklistItem(id=item_id, th="t", en="e", source_id=source_id)

    checklists = {
        "friends": (item("a", "shared"),),
        "tourism": (item("b", "tourism-only"), item("c", "shared"), item("d", "shared")),
        "family": (),
    }

    by_source = checklist_purposes_by_source(checklists)

    assert by_source == {"tourism-only": ("tourism",), "shared": ("tourism", "friends")}
    assert checklist_purposes(["tourism-only"], by_source) == ["tourism"]
    assert checklist_purposes(["shared", "tourism-only", "shared"], by_source) == ["tourism", "friends"]
    assert checklist_purposes(["not-linked"], by_source) == []
    assert checklist_purposes([], by_source) == []


@pytest.mark.parametrize("mode", ["anthropic", "ollama", "demo"])
def test_every_mode_uses_the_committed_checklists(settings: Settings, mode: str) -> None:
    from app.web.chat import checklist_purposes_by_source
    from tests.fakes.content import committed_checklists

    update = {"anthropic": {}, "ollama": {"llm_provider": "ollama"}, "demo": {"mock_llm": True}}[mode]
    created = create_app(settings.model_copy(update=update))

    assert created.state.checklist_purposes == checklist_purposes_by_source(committed_checklists())
    assert created.state.checklist_purposes[SPONSOR_FORM] == ("family", "friends")
    assert FEES not in created.state.checklist_purposes


def test_ollama_answer_citing_a_linked_source_names_its_checklists(settings: Settings) -> None:
    ollama = _ollama(settings)
    body = _ollama_stream(f"ผู้สนับสนุนกรอกแบบฟอร์ม [[{SPONSOR_FORM}]] ค่าธรรมเนียม [[{FEES}]].")
    client = _client(ollama, _ollama_llm(ollama, body))

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(
        _source(client, SPONSOR_FORM), _source(client, FEES), purposes=("family", "friends")
    )
