"""The `mock_llm` adapter: stored demo answers without an API key (Story 4.2)."""

import ast
import unicodedata
from pathlib import Path
from types import MappingProxyType

import pytest

from app.adapters.file_content import load_content
from app.adapters.file_demo_answers import DemoAnswer, DemoAnswers, load_demo_answers
from app.adapters.file_knowledge_base import load_knowledge_base
from app.adapters.mock_llm import MockLLM, done_key, normalise
from app.main import CONTENT_FILE, DEMO_ANSWERS_FILE, KNOWLEDGE_BASE_DIR
from app.ports.content import ExampleQuestion, FixedText
from app.ports.llm import AnswerChunk, LLMClient, Usage
from tests.fakes.content import committed_checklists

ZERO = Usage(0, 0, 0, 0)
CONTENT = load_content(CONTENT_FILE, "adviser@example.org", committed_checklists())
EXAMPLES = tuple(CONTENT.example_questions())
DEMO = load_demo_answers(DEMO_ANSWERS_FILE, EXAMPLES, load_knowledge_base(KNOWLEDGE_BASE_DIR))
MOCK_FILE = Path(__file__).resolve().parent.parent / "app" / "adapters" / "mock_llm.py"


@pytest.fixture
def mock() -> MockLLM:
    return MockLLM(DEMO, EXAMPLES, CONTENT.texts())


def _run(mock: MockLLM, question: str) -> list[AnswerChunk | Usage]:
    return list(mock.answer(question, ()))


def test_is_an_llm_client(mock: MockLLM) -> None:
    client: LLMClient = mock
    assert client is mock


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda q: q.id)
def test_example_streams_the_stored_answer_in_several_chunks(mock: MockLLM, example: ExampleQuestion) -> None:
    stored = DEMO.answers[example.id]

    items = _run(mock, example.th)

    *chunks, usage = items
    assert usage == ZERO
    assert len(chunks) > 1
    assert all(isinstance(c, AnswerChunk) and c.text for c in chunks)
    assert "".join(c.text for c in chunks) == stored.th
    assert chunks[0].source_ids == stored.source_ids
    assert all(c.source_ids == () for c in chunks[1:])


@pytest.mark.parametrize(
    "variant",
    [
        lambda q: f"  {q.th}  ",
        lambda q: q.th.replace(" ", "   \t"),
        lambda q: f"\n{q.th}\u00a0",
        lambda q: q.th.replace(" ", "\u00a0"),
        lambda q: unicodedata.normalize("NFD", q.th),
        lambda q: q.en,
        lambda q: f" {q.en.replace(' ', '  ')} ",
        lambda q: q.en.lower(),
        lambda q: q.en.upper(),
    ],
    ids=[
        "outer-spaces",
        "inner-spaces",
        "newline-trailing-nbsp",
        "inner-nbsp",
        "nfd",
        "english",
        "english-spaces",
        "english-lower-case",
        "english-upper-case",
    ],
)
def test_spacing_unicode_form_and_english_match(mock: MockLLM, variant) -> None:
    example = EXAMPLES[1]
    assert " " in example.th  # the inner-space variants need a space to change
    items = _run(mock, variant(example))

    assert "".join(c.text for c in items if isinstance(c, AnswerChunk)) == DEMO.answers[example.id].th


def test_nfd_input_matches_after_nfc() -> None:
    # Thai has no canonical decompositions, so check NFC with a composed letter.
    example = ExampleQuestion(id="q", th="ค่า café", en="cafe fee")
    demo = DemoAnswers(
        answers=MappingProxyType(
            {"q": DemoAnswer("q", "general", "ตอบ หนึ่ง สอง สาม สี่", "answer", ("udi-fees",))}
        ),
        done_phrases=("ok",),
    )
    texts = {"reply-demo-only": FixedText("เฉพาะ", "only")}
    mock = MockLLM(demo, (example,), texts)

    items = list(mock.answer(unicodedata.normalize("NFD", "ค่า  café"), ()))

    assert items[0] == AnswerChunk("ตอบ หนึ่ง สอง ", ("udi-fees",))


def test_stored_answer_pauses_between_chunks_only(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[str] = []
    sleeps: list[tuple[float, int]] = []
    monkeypatch.setattr(
        "app.adapters.mock_llm.time.sleep", lambda seconds: sleeps.append((seconds, len(received)))
    )
    mock = MockLLM(DEMO, EXAMPLES, CONTENT.texts(), pause_seconds=0.25)

    for item in mock.answer(EXAMPLES[0].th, ()):
        if isinstance(item, AnswerChunk):
            received.append(item.text)

    assert len(received) > 1
    # One pause before each chunk after the first: none before the first, none after the last.
    assert sleeps == [(0.25, n) for n in range(1, len(received))]


def test_other_question_does_not_pause(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr("app.adapters.mock_llm.time.sleep", sleeps.append)
    mock = MockLLM(DEMO, EXAMPLES, CONTENT.texts(), pause_seconds=0.25)

    assert list(mock.answer("hello", ())) == [ZERO]
    assert sleeps == []


@pytest.mark.parametrize("question", ["วีซ่าทำงานต้องใช้อะไร", "hello", EXAMPLES[0].th + " ไหม"])
def test_other_question_gets_no_text(mock: MockLLM, question: str) -> None:
    assert _run(mock, question) == [ZERO]


def test_history_does_not_change_the_answer(mock: MockLLM) -> None:
    from app.ports.llm import Exchange

    example = EXAMPLES[0]
    history = [Exchange(question=EXAMPLES[1].th, answer="x")]

    assert list(mock.answer(example.th, history)) == _run(mock, example.th)


@pytest.mark.parametrize(
    "phrase",
    [
        "ขอบคุณค่ะ",
        " ขอบคุณค่ะ ",
        "Thank  you",
        "OK",
        "Thanks!",
        "ok.",
        "ขอบคุณค่ะ 🙏",
        "ขอบคุณค่ะ🙏🏽",  # skin tone modifier
        "👍 ok",
        "ok 👍️",  # with a variation selector
        "«thank you»",
        "ขอบคุณครับ!!! 😊😊",
        "...okay...",
        "ได้ค่ะ",
        "ขอบคุณมากๆ ค่ะ",
    ],
)
def test_done_phrase_classifies_as_done(mock: MockLLM, phrase: str) -> None:
    assert mock.classify(phrase, []) == ("done", ZERO)


@pytest.mark.parametrize(
    "question",
    ["ขอบคุณค่ะ แล้ววีซ่าทำงานล่ะ", "thanks, and the fee?", "ok?? how much is the fee", "🙏", "!!!", "ok ok"],
)
def test_not_only_a_done_phrase_is_not_done(mock: MockLLM, question: str) -> None:
    assert mock.classify(question, []) == ("general", ZERO)


def test_example_question_gets_its_stored_category(mock: MockLLM) -> None:
    assert mock.classify(EXAMPLES[0].th, []) == (DEMO.answers[EXAMPLES[0].id].category, ZERO)


def test_stored_category_other_than_general_is_returned() -> None:
    example = ExampleQuestion(id="q", th="จะได้วีซ่าไหม", en="Will I get the visa?")
    demo = DemoAnswers(
        answers=MappingProxyType(
            {"q": DemoAnswer("q", "individual_assessment", "ตอบ", "answer", ("udi-fees",))}
        ),
        done_phrases=("ok",),
    )
    mock = MockLLM(demo, (example,), {"reply-demo-only": FixedText("เฉพาะ", "only")})

    assert mock.classify("จะได้วีซ่าไหม", []) == ("individual_assessment", ZERO)
    assert mock.classify("will i get the visa?", []) == ("individual_assessment", ZERO)


def test_emoji_only_done_phrase_does_not_make_every_emoji_only_message_done() -> None:
    # "🙏" alone has an empty done key; it must not match "👍", "!!!" or an empty key.
    demo = DemoAnswers(
        answers=MappingProxyType({"q": DemoAnswer("q", "general", "ตอบ", "answer", ("udi-fees",))}),
        done_phrases=("🙏", "ok"),
    )
    example = ExampleQuestion(id="q", th="ถาม", en="ask")
    mock = MockLLM(demo, (example,), {"reply-demo-only": FixedText("เฉพาะ", "only")})

    for message in ("🙏", "👍", "!!!", "🙏🙏"):
        assert mock.classify(message, []) == ("general", ZERO), message
    assert mock.classify("ok 🙏", []) == ("done", ZERO)


def test_done_key_trims_only_the_ends() -> None:
    assert done_key("  Thanks!  ") == "thanks"
    assert done_key("ขอบคุณค่ะ 🙏") == "ขอบคุณค่ะ"
    assert done_key("thanks, and the fee?") == "thanks, and the fee"
    # A Thai tone mark at the end is part of the word, not punctuation.
    assert done_key("ได้!") == "ได้"
    assert done_key("🙏👍") == ""


@pytest.mark.parametrize("example", EXAMPLES, ids=lambda q: q.id)
def test_translate_a_stored_answer(mock: MockLLM, example: ExampleQuestion) -> None:
    stored = DEMO.answers[example.id]

    assert mock.translate(stored.th) == (stored.en, ZERO)
    assert mock.translate(f"  {stored.th}\n") == (stored.en, ZERO)


@pytest.mark.parametrize("key", sorted(CONTENT.texts()))
def test_translate_a_fixed_text(mock: MockLLM, key: str) -> None:
    text = CONTENT.texts()[key]

    assert mock.translate(text.th) == (text.en, ZERO)


def test_translate_unknown_text_gives_demo_only_in_english(mock: MockLLM) -> None:
    assert mock.translate("ข้อความอื่น") == (CONTENT.texts()["reply-demo-only"].en, ZERO)


def test_normalise() -> None:
    assert normalise("  a \t\n b  c ") == "a b c"
    assert normalise(unicodedata.normalize("NFD", "é")) == "é"
    assert normalise("How Much") == "how much"


def test_mock_imports_no_sdk_or_network_library() -> None:
    tree = ast.parse(MOCK_FILE.read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])

    assert not modules & {"anthropic", "httpx", "requests", "urllib", "socket", "http"}
