from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ports.content import REQUIRED_TEXT_KEYS


def _get_texts(settings: Settings) -> dict:
    response = TestClient(create_app(settings)).get("/api/texts")
    assert response.status_code == 200
    return response.json()


def test_texts_shape_in_thai(settings: Settings) -> None:
    body = _get_texts(settings)

    assert set(body) == {"demo_mode", "texts", "example_questions"}
    assert body["demo_mode"] is False
    assert set(body["texts"]) == REQUIRED_TEXT_KEYS
    assert all(isinstance(v, str) and v for v in body["texts"].values())
    assert body["example_questions"]
    for question in body["example_questions"]:
        assert set(question) == {"id", "text"}
        assert any("\u0e00" <= ch <= "\u0e7f" for ch in question["text"])
    # Thai, not the stored English.
    assert body["texts"]["send-button"] == "ส่ง"


def test_texts_fill_adviser_contact(settings: Settings) -> None:
    custom = settings.model_copy(update={"adviser_contact": "test-adviser@example.org"})

    body = _get_texts(custom)

    assert "test-adviser@example.org" in body["texts"]["reply-no-answer"]
    assert "test-adviser@example.org" in body["texts"]["error"]
    assert not any("{ADVISER_CONTACT}" in v for v in body["texts"].values())


def test_demo_mode_follows_mock_llm(settings: Settings) -> None:
    demo = settings.model_copy(update={"mock_llm": True})

    assert _get_texts(demo)["demo_mode"] is True
