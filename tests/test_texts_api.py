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


def test_saved_chat_texts_are_served_in_thai(settings: Settings) -> None:
    texts = _get_texts(settings)["texts"]

    for key in (
        "history-button",
        "new-chat-button",
        "history-title",
        "history-close",
        "history-empty",
        "delete-chat",
        "delete-all-chats",
        "confirm-delete-chat",
        "confirm-delete-all-chats",
    ):
        assert any("\u0e00" <= ch <= "\u0e7f" for ch in texts[key]), key
    # The privacy notice says the chats are also saved on this device until deleted.
    assert "บันทึกไว้ในเครื่องนี้ด้วยจนกว่าคุณจะลบ" in texts["privacy-notice"]


def test_embassy_decides_text_is_served_in_thai_without_contact_or_claims(settings: Settings) -> None:
    texts = _get_texts(settings)["texts"]

    text = texts["reply-embassy-decides"]
    assert any("\u0e00" <= ch <= "\u0e7f" for ch in text)
    assert "สถานทูต" in text  # the embassy
    # No fees, deadlines or other figures in a fixed reply.
    assert not any(ch.isdigit() for ch in text)
