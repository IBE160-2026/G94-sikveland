import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app
from app.ports.content import REQUIRED_TEXT_KEYS, VISIT_PURPOSES
from tests.fakes.content import committed_checklists


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
    # And that the server keeps only the Yes/No feedback answer with an anonymous number
    # and the time, never the chat text (Story 2.3).
    assert "เก็บเฉพาะคำตอบ ใช่ หรือ ไม่" in texts["privacy-notice"]
    assert "หมายเลขที่ไม่ระบุตัวตนและเวลา" in texts["privacy-notice"]
    assert "ไม่เก็บข้อความในแชท" in texts["privacy-notice"]


@pytest.mark.parametrize("key", ["reply-out-of-scope", "reply-reach-person"])
def test_out_of_scope_and_reach_person_texts_are_thai_with_the_adviser_contact(
    settings: Settings, key: str
) -> None:
    custom = settings.model_copy(update={"adviser_contact": "adviser@example.org"})
    text = _get_texts(custom)["texts"][key]

    assert any("\u0e00" <= ch <= "\u0e7f" for ch in text)
    assert "adviser@example.org" in text


def test_out_of_scope_text_names_short_stay_visas_to_norway(settings: Settings) -> None:
    text = _get_texts(settings)["texts"]["reply-out-of-scope"]

    assert "ระยะสั้น" in text and "นอร์เวย์" in text  # short-stay, Norway


def test_embassy_decides_text_is_served_in_thai_without_contact_or_claims(settings: Settings) -> None:
    texts = _get_texts(settings)["texts"]

    text = texts["reply-embassy-decides"]
    assert any("\u0e00" <= ch <= "\u0e7f" for ch in text)
    assert "สถานทูต" in text  # the embassy
    # No fees, deadlines or other figures in a fixed reply.
    assert not any(ch.isdigit() for ch in text)


@pytest.mark.parametrize(
    "key", ["feedback-question", "feedback-follow-up", "feedback-thanks", "feedback-yes", "feedback-no"]
)
def test_feedback_texts_are_served_in_thai(settings: Settings, key: str) -> None:
    text = _get_texts(settings)["texts"][key]

    assert any("\u0e00" <= ch <= "\u0e7f" for ch in text), key
    # No adviser contact, figures or claims about requirements in the feedback texts.
    assert not any(ch.isdigit() for ch in text), key
    assert "@" not in text, key


CHECKLIST_KEYS = (
    "checklist-button",
    "checklist-title",
    "checklist-choose-purpose",
    "checklist-purpose-tourism",
    "checklist-purpose-family",
    "checklist-purpose-friends",
    "checklist-back",
    "checklist-change-purpose",
    "checklist-not-applicable",
    "checklist-progress",
    "checklist-all-done",
    "checklist-loading",
    "checklist-retry",
    "checklist-open",
)


def test_checklist_texts_are_served_in_thai(settings: Settings) -> None:
    texts = _get_texts(settings)["texts"]

    assert set(CHECKLIST_KEYS) <= REQUIRED_TEXT_KEYS
    for key in CHECKLIST_KEYS:
        assert any("\u0e00" <= ch <= "\u0e7f" for ch in texts[key]), key
    # One name per visit purpose.
    for purpose in VISIT_PURPOSES:
        assert f"checklist-purpose-{purpose}" in texts
    # The page fills in the counts; nothing else is left in braces.
    progress = texts["checklist-progress"]
    assert "{done}" in progress and "{total}" in progress
    assert "{" not in progress.replace("{done}", "").replace("{total}", "")


def test_checklist_texts_have_their_english_meaning(settings: Settings) -> None:
    from app.adapters.file_content import load_content
    from app.main import CONTENT_FILE

    texts = load_content(CONTENT_FILE, settings.adviser_contact, committed_checklists()).texts()

    assert texts["checklist-button"].en == "Checklist"
    assert texts["checklist-open"].en == "Open checklist"
    assert texts["checklist-not-applicable"].en == "Doesn't apply to me"
    assert texts["checklist-progress"].en == "{done} of {total} ready"
    # All done is no promise that the application is complete.
    assert "The embassy decides" in texts["checklist-all-done"].en
    assert "สถานทูต" in texts["checklist-all-done"].th
    assert [texts[f"checklist-purpose-{p}"].en for p in VISIT_PURPOSES] == [
        "Tourism",
        "Visiting family",
        "Visiting friends",
    ]


def test_feedback_texts_have_their_english_meaning(settings: Settings) -> None:
    from app.adapters.file_content import load_content
    from app.main import CONTENT_FILE

    texts = load_content(CONTENT_FILE, settings.adviser_contact, committed_checklists()).texts()

    assert texts["feedback-question"].en == "Have you received all the information you need?"
    assert texts["feedback-follow-up"].en.startswith("What would you still like to know?")
    assert (texts["feedback-yes"].en, texts["feedback-no"].en) == ("Yes", "No")
