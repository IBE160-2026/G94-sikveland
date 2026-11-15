"""Demo mode end to end: `MOCK_LLM=true` without an API key (Story 4.2)."""

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.anthropic_llm import AnthropicLLM
from app.adapters.file_demo_answers import DemoContentError
from app.adapters.mock_llm import MockLLM
from app.config import Settings
from app.main import DEMO_ANSWERS_FILE, STATIC_DIR, create_app
from app.pipeline.filter import REMOVED_MARKER
from app.ports.llm import AnswerChunk, LLMError, Usage
from tests.fakes.fake_llm import ScriptedLLM


@pytest.fixture(autouse=True)
def no_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app.main, "DEMO_CHUNK_PAUSE_SECONDS", 0.0)


@pytest.fixture
def demo_settings(settings: Settings) -> Settings:
    return settings.model_copy(update={"mock_llm": True})


@pytest.fixture
def client(demo_settings: Settings) -> TestClient:
    return TestClient(create_app(demo_settings))


def _events(client: TestClient, question: str) -> list[dict[str, Any]]:
    response = client.post("/api/chat", json={"question": question, "history": []})
    assert response.status_code == 200
    return [json.loads(line) for line in response.text.splitlines()]


def _log(settings: Settings) -> list[dict[str, Any]]:
    return [
        json.loads(line) for line in Path(settings.request_log_path).read_text(encoding="utf-8").splitlines()
    ]


def _examples(client: TestClient) -> list[Any]:
    return list(client.app.state.content.example_questions())


def _demo_only(client: TestClient) -> str:
    return client.app.state.content.texts()["reply-demo-only"].th


def test_demo_mode_wires_the_mock_without_a_key(demo_settings: Settings) -> None:
    assert demo_settings.anthropic_api_key is None
    assert isinstance(create_app(demo_settings).state.llm, MockLLM)


def test_mock_is_wired_with_the_chunk_pause(demo_settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(app.main, "DEMO_CHUNK_PAUSE_SECONDS", 0.123)

    assert create_app(demo_settings).state.llm._pause_seconds == 0.123


def test_passed_in_llm_in_demo_mode_still_checks_the_file(
    demo_settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app.main, "DEMO_ANSWERS_FILE", tmp_path / "missing.yaml")

    with pytest.raises(DemoContentError, match="cannot read"):
        create_app(demo_settings, llm=ScriptedLLM())


def test_passed_in_llm_in_demo_mode_gets_demo_only_text_and_zero_cost(demo_settings: Settings) -> None:
    usage = Usage(input_tokens=1000, output_tokens=200, cache_read_tokens=50000, cache_write_tokens=10)
    llm = ScriptedLLM([AnswerChunk("an uncited guess")], usage=usage)
    client = TestClient(create_app(demo_settings, llm=llm))

    events = _events(client, "any question")

    assert client.app.state.llm is llm
    assert events[1] == {"type": "text", "delta": _demo_only(client)}
    [line] = _log(demo_settings)
    assert line["model"] == "mock_llm"
    assert line["input_tokens"] == 1000
    assert line["cost_usd"] == 0.0


def test_demo_line_without_usage_still_records_zero_cost(demo_settings: Settings) -> None:
    client = TestClient(create_app(demo_settings, llm=ScriptedLLM([], error=LLMError("boom"))))

    events = _events(client, "any question")

    assert events[-1] == {"type": "error", "key": "error"}
    [line] = _log(demo_settings)
    assert line["outcome"] == "error"
    assert line["model"] == "mock_llm"
    assert line["cost_usd"] == 0.0
    assert (line["input_tokens"], line["output_tokens"]) == (0, 0)


def test_every_example_streams_its_stored_answer_with_sources(client: TestClient) -> None:
    from app.adapters.file_demo_answers import load_demo_answers

    state = client.app.state
    demo = load_demo_answers(DEMO_ANSWERS_FILE, _examples(client), state.knowledge_base)
    for example in _examples(client):
        stored = demo.answers[example.id]

        events = _events(client, example.th)

        assert events[0] == {
            "type": "meta",
            "category": "general",
            "personal_info_removed": False,
            "clean_question": example.th,
        }
        texts = [e for e in events[1:-2]]
        assert len(texts) > 1 and all(e["type"] == "text" for e in texts)
        assert "".join(e["delta"] for e in texts) == stored.th
        expected = []
        for sid in stored.source_ids:
            source = state.knowledge_base.source(sid)
            expected.append({"id": source.id, "title": source.title, "url": source.url})
        assert events[-2] == {
            "type": "sources",
            "sources": expected,
            "checklist": False,
            "checklist_purposes": [],
        }
        assert events[-1] == {"type": "done"}


def test_spacing_and_english_get_the_same_answer(client: TestClient) -> None:
    example = _examples(client)[1]
    reference = _events(client, example.th)[1:]

    assert _events(client, f"  {example.th.replace(' ', '    ')} ")[1:] == reference
    assert _events(client, example.en)[1:] == reference


def test_other_question_gets_the_demo_only_text(client: TestClient, demo_settings: Settings) -> None:
    events = _events(client, "วีซ่าทำงานต้องใช้เอกสารอะไร")

    assert [e["type"] for e in events] == ["meta", "text", "sources", "done"]
    assert events[1]["delta"] == _demo_only(client)
    assert demo_settings.adviser_contact in events[1]["delta"]
    assert events[2]["sources"] == []


def test_personal_info_is_filtered_first_so_the_example_no_longer_matches(client: TestClient) -> None:
    example = _examples(client)[0]

    events = _events(client, f"{example.th} AA1234567")

    assert events[0]["personal_info_removed"] is True
    assert events[0]["clean_question"] == f"{example.th} {REMOVED_MARKER}"
    assert events[1] == {"type": "text", "delta": _demo_only(client)}
    assert events[2]["sources"] == []


def test_request_log_records_mock_llm_at_no_cost(client: TestClient, demo_settings: Settings) -> None:
    _events(client, _examples(client)[0].th)
    _events(client, "something else")

    lines = _log(demo_settings)
    assert [line["outcome"] for line in lines] == ["answered", "no_answer"]
    for line in lines:
        assert line["model"] == "mock_llm"
        assert line["cost_usd"] == 0.0
        assert (line["input_tokens"], line["output_tokens"]) == (0, 0)
        assert (line["cache_read_tokens"], line["cache_write_tokens"]) == (0, 0)


def test_texts_api_says_demo_mode(client: TestClient) -> None:
    body = client.get("/api/texts").json()

    assert body["demo_mode"] is True
    assert body["texts"]["demo-label"]


def test_page_shows_the_demo_label_always_visible() -> None:
    html = (Path(STATIC_DIR) / "index.html").read_text(encoding="utf-8")
    js = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")
    css = (Path(STATIC_DIR) / "style.css").read_text(encoding="utf-8")

    assert 'id="demo-label"' in html and "hidden" in html.split('id="demo-label"')[1].split(">")[0]
    assert 'demoLabel.textContent = data.texts["demo-label"];' in js
    assert "demoLabel.hidden = data.demo_mode !== true;" in js
    # The label sits in the top header, which stays at the top while scrolling.
    header = html.split('<header class="top">')[1].split("</header>")[0]
    assert 'id="demo-label"' in header
    rule = css.split(".top {")[1].split("}")[0]
    assert "position: sticky;" in rule and "top: 0;" in rule


def test_missing_demo_answer_stops_startup(
    demo_settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "demo-answers.yaml"
    path.write_text("answers: {}\ndone_phrases: [ok]\n", encoding="utf-8")
    monkeypatch.setattr(app.main, "DEMO_ANSWERS_FILE", path)

    with pytest.raises(DemoContentError, match="tourist-visa-documents"):
        create_app(demo_settings)


def test_unknown_source_stops_startup(
    demo_settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    text = DEMO_ANSWERS_FILE.read_text(encoding="utf-8").replace("- udi-fees", "- no-such-source", 1)
    path = tmp_path / "demo-answers.yaml"
    path.write_text(text, encoding="utf-8")
    monkeypatch.setattr(app.main, "DEMO_ANSWERS_FILE", path)

    with pytest.raises(DemoContentError, match="no-such-source") as caught:
        create_app(demo_settings)
    assert "visa-fee" in str(caught.value)


def test_real_mode_does_not_read_the_demo_answers(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(app.main, "DEMO_ANSWERS_FILE", tmp_path / "missing.yaml")

    created = create_app(settings)

    assert isinstance(created.state.llm, AnthropicLLM)
    assert created.state.answer_model == settings.model_answer
    assert created.state.no_answer_key == "reply-no-answer"
