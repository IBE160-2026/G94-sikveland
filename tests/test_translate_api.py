"""`POST /api/translate`: the English of one finished reply (Story 4.1, FR7, AD-4).

Every row of the I/O matrix in docs/implementation/spec-4-1-show-the-english-translation.md
that the server owns. The model is always `ScriptedLLM` or an adapter over a stand-in
transport: no test makes a network call.
"""

import json
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

import app.main
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.file_prompts import PromptError, load_prompt
from app.adapters.ollama_llm import OllamaLLM
from app.config import Settings
from app.main import create_app
from app.pipeline.cost import cost_usd
from app.pipeline.filter import REMOVED_MARKER
from app.pipeline.translate import lookup_key, normalise, stored_english, translate_reply
from app.ports.content import ExampleQuestion, FixedText
from app.ports.llm import LLMError, LLMRefusalError, Usage
from app.web.request_log import small_prices
from tests.fakes.fake_llm import TRANSLATE_USAGE, ScriptedLLM

ENVELOPE_KEYS = {"code", "message"}
MODEL_ANSWER = "ค่าธรรมเนียมวีซ่าคือ 90 ยูโร\nชำระที่ VFS Global"
FAILED = {"error": {"code": "translation_failed", "message": "the text could not be translated"}}
WRONG_MEDIA_TYPE = {
    "error": {"code": "unsupported_media_type", "message": "Content-Type must be application/json"}
}
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


def _client(settings: Settings, llm: Any) -> TestClient:
    return TestClient(create_app(settings, llm=llm))


def _post(client: TestClient, text: Any) -> Any:
    return client.post("/api/translate", json={"text": text})


def _log(settings: Settings) -> list[dict[str, Any]]:
    path = Path(settings.request_log_path)
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def _texts(client: TestClient) -> dict[str, FixedText]:
    return dict(client.app.state.content.texts())


def _examples(client: TestClient) -> list[ExampleQuestion]:
    return list(client.app.state.content.example_questions())


# --- stored English: no model call, no log line ------------------------------------------


@pytest.mark.parametrize(
    "spacing",
    [
        lambda th: th,
        lambda th: f"  \n{th}\t ",
        lambda th: th.replace(" ", "   ").replace("\n", " "),
        lambda th: " ".join(th.split()),
    ],
    ids=["as-is", "padded", "extra-spaces", "collapsed"],
)
def test_fixed_reply_gets_its_stored_english_with_any_spacing(settings: Settings, spacing: Any) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)
    text = _texts(client)["reply-embassy-decides"]

    response = _post(client, spacing(text.th))

    assert response.status_code == 200
    assert response.json() == {"translation": text.en}
    assert llm.translate_calls == []
    assert _log(settings) == []


def test_every_fixed_text_gets_its_stored_english(settings: Settings) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    for key, text in _texts(client).items():
        assert _post(client, text.th).json() == {"translation": text.en}, key

    assert llm.translate_calls == []
    assert _log(settings) == []


def test_every_example_question_gets_its_stored_english(settings: Settings) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    for example in _examples(client):
        assert _post(client, example.th).json() == {"translation": example.en}, example.id

    assert llm.translate_calls == []
    assert _log(settings) == []


def test_reach_person_reply_with_the_contact_filled_in_gets_its_stored_english(settings: Settings) -> None:
    settings = settings.model_copy(update={"adviser_contact": "adviser@example.org"})
    llm = ScriptedLLM()
    client = _client(settings, llm)
    text = _texts(client)["reply-reach-person"]
    # The page shows (and sends) the reply with the contact, never the placeholder.
    assert "adviser@example.org" in text.th and "{ADVISER_CONTACT}" not in text.th

    response = _post(client, text.th)

    assert response.json() == {"translation": text.en}
    assert "adviser@example.org" in text.en
    assert llm.translate_calls == []


def test_reply_with_text_added_to_a_fixed_text_goes_to_the_model(settings: Settings) -> None:
    llm = ScriptedLLM(translation="Other English")
    client = _client(settings, llm)
    thai = _texts(client)["reply-embassy-decides"].th + " เพิ่มเติม"

    assert _post(client, thai).json() == {"translation": "Other English"}
    assert llm.translate_calls == [thai]


# --- the model path ------------------------------------------------------------------------


def test_model_answer_is_translated_by_the_llm_and_logged_with_small_model_usage(settings: Settings) -> None:
    llm = ScriptedLLM(translation="The visa fee is 90 euros.\nPay at VFS Global.")
    client = _client(settings, llm)

    response = _post(client, MODEL_ANSWER)

    assert response.status_code == 200
    assert response.json() == {"translation": "The visa fee is 90 euros.\nPay at VFS Global."}
    assert llm.translate_calls == [MODEL_ANSWER]
    # No answer or classify call: only the translation.
    assert llm.calls == [] and llm.classify_calls == []
    [line] = _log(settings)
    assert set(line) == LOG_FIELDS
    assert {k: v for k, v in line.items() if k != "timestamp"} == {
        "endpoint": "translate",
        "outcome": "translated",
        "category": None,
        "prompt_versions": {"translate": client.app.state.translate_prompt.version},
        "model": settings.model_small,
        "input_tokens": TRANSLATE_USAGE.input_tokens,
        "output_tokens": TRANSLATE_USAGE.output_tokens,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "classify_input_tokens": None,
        "classify_output_tokens": None,
        "cost_usd": cost_usd(TRANSLATE_USAGE, small_prices(settings)),
        "unknown_source_ids": None,
    }
    assert line["cost_usd"] > 0


def test_the_log_line_holds_no_text(settings: Settings) -> None:
    llm = ScriptedLLM(translation="SECRET-ENGLISH")
    client = _client(settings, llm)

    _post(client, "ข้อความลับ SECRET-THAI")

    content = Path(settings.request_log_path).read_text(encoding="utf-8")
    assert "SECRET" not in content and "ข้อความลับ" not in content


def test_text_is_stripped_and_the_translation_too(settings: Settings) -> None:
    llm = ScriptedLLM(translation="\n  Hello.  \n")
    client = _client(settings, llm)

    response = _post(client, "   สวัสดี \n")

    assert response.json() == {"translation": "Hello."}
    assert llm.translate_calls == ["สวัสดี"]


def test_ten_thousand_characters_are_accepted(settings: Settings) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    assert _post(client, "ก" * 10000).status_code == 200
    assert llm.translate_calls == ["ก" * 10000]


@pytest.mark.parametrize(
    ("text", "sent"),
    [
        ("เลขพาสปอร์ตของฉันคือ AA1234567 ค่ะ", f"เลขพาสปอร์ตของฉันคือ {REMOVED_MARKER} ค่ะ"),
        ("บัตรประชาชน 1-2345-67890-12-3 ครับ", f"บัตรประชาชน {REMOVED_MARKER} ครับ"),
    ],
    ids=["passport", "thai-id"],
)
def test_personal_info_is_removed_before_the_model_sees_it(settings: Settings, text: str, sent: str) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    assert _post(client, text).status_code == 200
    assert llm.translate_calls == [sent]
    assert "AA1234567" not in Path(settings.request_log_path).read_text(encoding="utf-8")


def test_fixed_text_with_personal_info_added_is_not_the_stored_text(settings: Settings) -> None:
    llm = ScriptedLLM(translation="x")
    client = _client(settings, llm)
    thai = _texts(client)["reply-embassy-decides"].th

    _post(client, f"{thai} AA1234567")

    assert llm.translate_calls == [f"{thai} {REMOVED_MARKER}"]


# --- failures ------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "error",
    [
        LLMError("translate call failed: APIConnectionError"),
        LLMRefusalError("the model refused to translate"),
        NotImplementedError("not built"),
        RuntimeError("unexpected SECRET-THAI"),
    ],
    ids=["llm-error", "refusal", "not-implemented", "other"],
)
def test_model_failure_is_502_and_logged_as_error_without_usage(
    settings: Settings, error: Exception, caplog: pytest.LogCaptureFixture
) -> None:
    llm = ScriptedLLM(translate_error=error)
    client = _client(settings, llm)

    with caplog.at_level(logging.INFO):
        response = _post(client, "ข้อความ SECRET-THAI")

    assert response.status_code == 502
    assert response.json() == FAILED
    [line] = _log(settings)
    assert (line["endpoint"], line["outcome"], line["category"]) == ("translate", "error", None)
    assert line["model"] == settings.model_small
    assert line["prompt_versions"] == {"translate": client.app.state.translate_prompt.version}
    for field in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens", "cost_usd"):
        assert line[field] is None, field
    # The text is never logged or echoed, not even through an error message.
    assert "SECRET" not in caplog.text and "SECRET" not in response.text
    assert "ข้อความ" not in caplog.text


@pytest.mark.parametrize("translation", ["", "   \n "])
def test_empty_translation_is_502(settings: Settings, translation: str) -> None:
    client = _client(settings, ScriptedLLM(translation=translation))

    response = _post(client, MODEL_ANSWER)

    assert response.status_code == 502
    assert response.json() == FAILED
    assert [line["outcome"] for line in _log(settings)] == ["error"]


def test_claude_without_a_key_is_502_and_makes_no_call(settings: Settings) -> None:
    # The real adapter without ANTHROPIC_API_KEY: it fails before any network use.
    assert settings.anthropic_api_key is None
    client = TestClient(create_app(settings))

    response = _post(client, MODEL_ANSWER)

    assert response.status_code == 502
    assert response.json() == FAILED
    [line] = _log(settings)
    assert (line["outcome"], line["model"]) == ("error", settings.model_small)


def test_a_failing_request_log_never_breaks_the_translation(settings: Settings) -> None:
    class BrokenLog:
        def write(self, line: Any) -> None:
            raise OSError("disk full")

    client = _client(settings, ScriptedLLM(translation="Hello"))
    client.app.state.request_log = BrokenLog()

    assert _post(client, MODEL_ANSWER).json() == {"translation": "Hello"}


# --- bad requests --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "body",
    [
        {},
        {"text": ""},
        {"text": "   \n\t "},
        {"text": "ก" * 10001},
        {"text": "สวัสดี", "extra": 1},
        {"text": "สวัสดี", "history": []},
        {"text": 123},
        {"text": None},
        {"text": ["สวัสดี"]},
        ["สวัสดี"],
        "สวัสดี",
    ],
    ids=[
        "empty-object",
        "empty",
        "whitespace",
        "too-long",
        "extra-field",
        "extra-history",
        "number",
        "null",
        "list",
        "list-body",
        "string-body",
    ],
)
def test_bad_body_is_422_with_the_envelope_and_no_call(settings: Settings, body: Any) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    response = client.post("/api/translate", json=body)

    assert response.status_code == 422
    assert set(response.json()) == {"error"}
    assert set(response.json()["error"]) == ENVELOPE_KEYS
    assert response.json()["error"]["code"] == "invalid_request"
    assert "สวัสดี" not in response.text and "extra" not in response.text.replace("extra_forbidden", "")
    assert llm.translate_calls == []
    assert _log(settings) == []


@pytest.mark.parametrize("content", [b"not json", b'{"text": "a"', b"", b"\xff\xfe"])
def test_body_that_is_not_json_is_422(settings: Settings, content: bytes) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    response = client.post("/api/translate", content=content, headers={"Content-Type": "application/json"})

    assert response.status_code == 422
    assert set(response.json()["error"]) == ENVELOPE_KEYS
    assert llm.translate_calls == []


VALID_BODY = json.dumps({"text": "สวัสดี"}).encode()


@pytest.mark.parametrize(
    "headers",
    [
        {},
        {"Content-Type": "text/plain"},
        {"Content-Type": "text/plain;charset=UTF-8"},
        {"Content-Type": "application/x-www-form-urlencoded"},
        {"Content-Type": "multipart/form-data; boundary=x"},
        {"Content-Type": "application/merge-patch+json"},
    ],
    ids=["no-content-type", "text-plain", "text-plain-charset", "form", "multipart", "plus-json"],
)
def test_wrong_media_type_is_415_and_makes_no_call(settings: Settings, headers: dict[str, str]) -> None:
    llm = ScriptedLLM()
    client = _client(settings, llm)

    response = client.post("/api/translate", content=VALID_BODY, headers=headers)

    assert response.status_code == 415
    assert response.json() == WRONG_MEDIA_TYPE
    assert llm.translate_calls == []
    assert _log(settings) == []


@pytest.mark.parametrize("content_type", ["application/json; charset=utf-8", "Application/JSON"])
def test_json_content_type_with_parameters_or_any_case_is_accepted(
    settings: Settings, content_type: str
) -> None:
    llm = ScriptedLLM(translation="Hello")
    client = _client(settings, llm)

    response = client.post("/api/translate", content=VALID_BODY, headers={"Content-Type": content_type})

    assert response.json() == {"translation": "Hello"}


# --- per mode ------------------------------------------------------------------------------


def _ollama_reply(content: str) -> bytes:
    return json.dumps(
        {
            "model": "qwen-test",
            "message": {"role": "assistant", "content": content},
            "done": True,
            "done_reason": "stop",
            "prompt_eval_count": 700,
            "eval_count": 90,
        },
        ensure_ascii=False,
    ).encode()


def _ollama(settings: Settings, handler: Any) -> OllamaLLM:
    return OllamaLLM(
        settings,
        load_knowledge_base(app.main.KNOWLEDGE_BASE_DIR),
        load_prompt(app.main.ANSWER_PROMPT_FILE),
        load_prompt(app.main.CITING_PROMPT_FILE),
        load_prompt(app.main.CLASSIFIER_PROMPT_FILE),
        load_prompt(app.main.TRANSLATE_PROMPT_FILE),
        client=httpx.Client(transport=httpx.MockTransport(handler)),
    )


@pytest.fixture
def ollama_settings(settings: Settings) -> Settings:
    return settings.model_copy(
        update={
            "llm_provider": "ollama",
            "ollama_base_url": "http://ollama.test:11434",
            "ollama_model": "qwen-test",
        }
    )


def test_ollama_translates_with_its_model_at_no_cost(ollama_settings: Settings) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=_ollama_reply("  The fee is 90 euros. "))

    client = _client(ollama_settings, _ollama(ollama_settings, handler))

    response = _post(client, f"{MODEL_ANSWER} AA1234567")

    assert response.json() == {"translation": "The fee is 90 euros."}
    [request] = requests
    body = json.loads(request.content)
    assert body["model"] == "qwen-test" and body["think"] is False and body["stream"] is False
    assert body["messages"][0] == {"role": "system", "content": client.app.state.translate_prompt.text}
    assert body["messages"][1] == {"role": "user", "content": f"{MODEL_ANSWER} {REMOVED_MARKER}"}
    [line] = _log(ollama_settings)
    assert (line["endpoint"], line["outcome"], line["model"]) == ("translate", "translated", "qwen-test")
    assert (line["input_tokens"], line["output_tokens"], line["cost_usd"]) == (700, 90, 0.0)
    assert line["prompt_versions"] == {"translate": client.app.state.translate_prompt.version}


def test_ollama_stored_text_needs_no_call(ollama_settings: Settings) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise AssertionError("Ollama called")

    client = _client(ollama_settings, _ollama(ollama_settings, handler))
    text = _texts(client)["reply-out-of-scope"]

    assert _post(client, text.th).json() == {"translation": text.en}
    assert _log(ollama_settings) == []


@pytest.mark.parametrize(
    "reply",
    [
        httpx.Response(200, content=b'{"error": "model not found"}'),
        httpx.Response(200, content=_ollama_reply("")),
        httpx.Response(404, content=b"{}"),
    ],
    ids=["error-field", "empty", "http-404"],
)
def test_ollama_failure_is_502(ollama_settings: Settings, reply: httpx.Response) -> None:
    client = _client(ollama_settings, _ollama(ollama_settings, lambda request: reply))

    response = _post(client, MODEL_ANSWER)

    assert response.status_code == 502
    assert response.json() == FAILED
    [line] = _log(ollama_settings)
    assert (line["outcome"], line["model"], line["cost_usd"]) == ("error", "qwen-test", None)


def test_ollama_mode_with_a_given_llm_is_priced_at_zero(ollama_settings: Settings) -> None:
    usage = Usage(input_tokens=1000, output_tokens=500, cache_read_tokens=0, cache_write_tokens=0)
    client = _client(ollama_settings, ScriptedLLM(translate_usage=usage))

    _post(client, MODEL_ANSWER)

    [line] = _log(ollama_settings)
    assert (line["model"], line["input_tokens"], line["cost_usd"]) == ("qwen-test", 1000, 0.0)


def test_wired_claude_adapter_sends_the_translate_prompt(settings: Settings) -> None:
    from pydantic import SecretStr

    sent: list[dict[str, Any]] = []

    def create(**kwargs: Any) -> Any:
        sent.append(kwargs)
        usage = SimpleNamespace(
            input_tokens=10, output_tokens=5, cache_read_input_tokens=None, cache_creation_input_tokens=None
        )
        content = [SimpleNamespace(type="text", text="Hello")]
        return SimpleNamespace(stop_reason="end_turn", usage=usage, content=content)

    created = create_app(settings.model_copy(update={"anthropic_api_key": SecretStr("sk-test")}))
    created.state.llm._client = SimpleNamespace(messages=SimpleNamespace(create=create))

    response = _post(TestClient(created), MODEL_ANSWER)

    assert response.json() == {"translation": "Hello"}
    [request] = sent
    assert request["system"] == load_prompt(app.main.TRANSLATE_PROMPT_FILE).text
    assert request["model"] == settings.model_small


def test_wired_ollama_adapter_sends_the_translate_prompt(ollama_settings: Settings) -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, content=_ollama_reply("Hello"))

    created = create_app(ollama_settings)
    created.state.llm._client = httpx.Client(transport=httpx.MockTransport(handler))

    response = _post(TestClient(created), MODEL_ANSWER)

    assert response.json() == {"translation": "Hello"}
    [request] = requests
    messages = json.loads(request.content)["messages"]
    assert messages[0] == {"role": "system", "content": load_prompt(app.main.TRANSLATE_PROMPT_FILE).text}


@pytest.mark.parametrize("mock_llm", [False, True], ids=["claude", "demo"])
def test_a_broken_translate_prompt_stops_startup_in_every_mode(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mock_llm: bool
) -> None:
    monkeypatch.setattr(app.main, "TRANSLATE_PROMPT_FILE", tmp_path / "missing.md")

    with pytest.raises(PromptError):
        create_app(settings.model_copy(update={"mock_llm": mock_llm}), llm=ScriptedLLM())


def test_a_translate_prompt_without_a_version_stops_startup(
    settings: Settings, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prompt = tmp_path / "translate.md"
    prompt.write_text("Translate to English.\n", encoding="utf-8")
    monkeypatch.setattr(app.main, "TRANSLATE_PROMPT_FILE", prompt)

    with pytest.raises(PromptError):
        create_app(settings, llm=ScriptedLLM())


def test_chat_prompt_versions_never_include_translate(settings: Settings) -> None:
    client = _client(settings, ScriptedLLM())

    assert "translate" not in client.app.state.prompt_versions


# --- the pure pipeline ---------------------------------------------------------------------


def test_normalise_is_nfc_with_whitespace_collapsed_and_trimmed() -> None:
    import unicodedata

    assert normalise("  a \t\n b  c ") == "a b c"
    assert normalise(unicodedata.normalize("NFD", "é")) == "é"
    # Thai has no case; Latin case is kept (unlike the demo adapter's own lookup).
    assert normalise("VFS Global") == "VFS Global"


def test_stored_english_keys_the_filtered_normalised_thai_and_the_first_wins() -> None:
    texts = {
        "a": FixedText(th="  ข้อความ   หนึ่ง ", en="One"),
        "b": FixedText(th="ข้อความ หนึ่ง", en="Duplicate"),
    }
    questions = [ExampleQuestion(id="q", th="คำถาม\nสอง", en="Two")]

    stored = stored_english(texts, questions)

    assert stored == {"ข้อความ หนึ่ง": "One", "คำถาม สอง": "Two"}
    assert lookup_key(" คำถาม  สอง ") == "คำถาม สอง"


def test_translate_reply_returns_the_stored_english_without_usage() -> None:
    llm = ScriptedLLM()

    result = translate_reply(" ข้อความ \n หนึ่ง ", llm, {"ข้อความ หนึ่ง": "One"})

    assert (result.text, result.usage, result.stored) == ("One", None, True)
    assert llm.translate_calls == []


def test_translate_reply_sends_the_filtered_text_to_the_model() -> None:
    llm = ScriptedLLM(translation=" Two ")

    result = translate_reply("อื่น AA1234567", llm, {})

    assert (result.text, result.usage, result.stored) == ("Two", TRANSLATE_USAGE, False)
    assert llm.translate_calls == [f"อื่น {REMOVED_MARKER}"]
