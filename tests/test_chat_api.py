"""`POST /api/chat`: the JSON Lines stream contract (AD-8) with a scripted model."""

import json
import logging
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_prompts import PromptError
from app.config import ROOT, Settings
from app.main import create_app
from app.pipeline.filter import REMOVED_MARKER
from app.ports.llm import AnswerChunk, Exchange, LLMError, Usage
from tests.fakes.fake_llm import ScriptedLLM

S1 = "embassy-necessary-documents"
S2 = "embassy-online-registration"
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


def _sources(*items: dict[str, str]) -> dict[str, Any]:
    return {"type": "sources", "sources": list(items), "checklist": False, "checklist_purposes": []}


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
        _sources(_source(client, S1)),
        DONE,
    ]


def test_sources_in_first_cited_order_each_once(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("x", (S2,)), AnswerChunk("y", (S1, S2)), AnswerChunk("z", (S1,))])
    client = _client(settings, llm)

    events = _events(client, {"question": QUESTION, "history": []})

    assert events[-2] == _sources(_source(client, S2), _source(client, S1))


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


def test_unknown_cited_id_ends_with_error(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("A", ("no-such-source",))])

    assert _events(_client(settings, llm), {"question": QUESTION, "history": []}) == [_meta(), ERROR]


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

    assert events == [_meta(), ERROR]


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
    "outcome",
    "category",
    "prompt_versions",
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cost_usd",
}
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
        "outcome": "answered",
        "category": "general",
        "prompt_versions": {"answer": client.app.state.answer_prompt.version},
        "model": settings.model_answer,
        "input_tokens": 1000,
        "output_tokens": 200,
        "cache_read_tokens": 50000,
        "cache_write_tokens": 0,
        # (1000x4 + 200x20 + 50000x0.2 + 0x5) / 1e6 with the default prices
        "cost_usd": 0.018,
    }


def test_no_answer_logs_no_answer_with_tokens_and_cost(settings: Settings) -> None:
    llm = ScriptedLLM([AnswerChunk("uncited")], usage=SPEC_USAGE)

    _events(_client(settings, llm), {"question": QUESTION, "history": []})

    [line] = _log(settings)
    assert line["outcome"] == "no_answer"
    assert (line["input_tokens"], line["cost_usd"]) == (1000, 0.018)


@pytest.mark.parametrize(
    "llm",
    [
        ScriptedLLM([], error=LLMError("boom")),
        ScriptedLLM([AnswerChunk("A", (S1,))], error=LLMError("cut")),
        ScriptedLLM([], refusal=True),
        ScriptedLLM([AnswerChunk("A", ("no-such-source",))]),
        _Exploding(),
    ],
    ids=["error-before-text", "error-after-text", "refusal", "unknown-source", "unexpected"],
)
def test_error_logs_error_with_null_tokens_and_cost(settings: Settings, llm: ScriptedLLM) -> None:
    events = _events(_client(settings, llm), {"question": QUESTION, "history": []})

    assert events[-1] == ERROR
    [line] = _log(settings)
    assert set(line) == LOG_FIELDS
    assert line["outcome"] == "error"
    assert line["category"] == "general"
    for field in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "cost_usd"):
        assert line[field] is None, field


def test_client_gone_mid_answer_logs_incomplete(settings: Settings) -> None:
    from app.pipeline.answer import answer_question
    from app.web.chat import _lines

    logged: list[tuple[Any, ...]] = []
    llm = ScriptedLLM([AnswerChunk("A", (S1,)), AnswerChunk("B"), AnswerChunk("C")], usage=SPEC_USAGE)
    kb = create_app(settings, llm=llm).state.knowledge_base
    events = answer_question(QUESTION, (), llm, kb, "no answer")
    lines = _lines(events, lambda *args: logged.append(args))

    assert json.loads(next(lines))["type"] == "meta"
    assert json.loads(next(lines)) == {"type": "text", "delta": "A"}
    assert logged == []
    # Simulates the close that garbage collection performs on the abandoned stream
    # when the client goes away (Starlette does not close it itself).
    lines.close()

    assert logged == [("incomplete", "general", None)]
    assert events.gi_frame is None  # the pipeline (and the model stream) is closed too


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

    assert first == second == [_meta(), {"type": "text", "delta": "A"}, _sources(_source(client, S1)), DONE]
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
