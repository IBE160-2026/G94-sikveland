"""`POST /api/chat`: the JSON Lines stream contract (AD-8) with a scripted model."""

import json
import logging
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_prompts import PromptError
from app.config import Settings
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
