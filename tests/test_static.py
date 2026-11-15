import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import STATIC_DIR, create_app

THAI = re.compile("[\u0e00-\u0e7f]")
# Text assets only: binary files (icons, fonts) cannot hold Thai text or links.
TEXT_SUFFIXES = {".html", ".css", ".js"}
STATIC_FILES = sorted(p for p in Path(STATIC_DIR).rglob("*") if p.is_file() and p.suffix in TEXT_SUFFIXES)
# An absolute or protocol-relative URL (`https://`, `//`) used as a resource:
# in an HTML attribute (double, single or no quotes), a CSS url(...) or @import,
# or a JS fetch(...).
EXTERNAL = re.compile(
    r"""(?:\b(?:src|href|action)\s*=\s*["']?"""
    r"""|\burl\(\s*["']?"""
    r"""|@import\s+(?:url\(\s*)?["']?"""
    r"""|\bfetch\(\s*["'`]?)"""
    r"""(?:[a-z][a-z0-9+.-]*:)?//""",
    re.IGNORECASE,
)


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))


def test_root_serves_the_chat_page(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert '<html lang="th">' in html
    assert '<meta name="viewport" content="width=device-width, initial-scale=1">' in html
    assert 'src="/app.js"' in html and 'href="/style.css"' in html
    # Retry button for when /api/texts cannot be loaded: a symbol, no words.
    assert 'id="retry"' in html


@pytest.mark.parametrize(("path", "kind"), [("/app.js", "javascript"), ("/style.css", "text/css")])
def test_assets_are_served(client: TestClient, path: str, kind: str) -> None:
    response = client.get(path)

    assert response.status_code == 200
    assert kind in response.headers["content-type"]


def test_api_routes_win_over_static_files(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}
    assert client.get("/api/texts").status_code == 200


def test_static_folder_has_the_page_files() -> None:
    names = {p.name for p in STATIC_FILES}
    assert {"index.html", "style.css", "app.js"} <= names


@pytest.mark.parametrize("path", STATIC_FILES, ids=lambda p: p.name)
def test_no_thai_in_static_files(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    assert not THAI.search(text), f"Thai text in {path.name}; put it in content/texts.yaml"


@pytest.mark.parametrize("path", STATIC_FILES, ids=lambda p: p.name)
def test_page_uses_no_external_resources(path: Path) -> None:
    match = EXTERNAL.search(path.read_text(encoding="utf-8"))

    assert match is None, f"external resource in {path.name}: {match and match.group(0)}"


@pytest.mark.parametrize(
    "snippet",
    [
        '<script src="https://cdn.example.com/x.js">',
        "<link href='//cdn.example.com/x.css'>",
        "<img src=https://cdn.example.com/x.png>",
        "body { background: url(//cdn.example.com/x.png); }",
        "@font-face { src: url('https://cdn.example.com/f.woff2'); }",
        '@import "https://cdn.example.com/x.css";',
        "@import url(https://cdn.example.com/x.css);",
        'fetch("https://api.example.com/texts")',
        "fetch(`//api.example.com/texts`)",
    ],
)
def test_external_resource_pattern_catches(snippet: str) -> None:
    assert EXTERNAL.search(snippet)


@pytest.mark.parametrize(
    "snippet",
    ['<script src="/app.js">', "url(/img.png)", 'fetch("/api/texts")', "// a comment"],
)
def test_external_resource_pattern_allows_local(snippet: str) -> None:
    assert not EXTERNAL.search(snippet)


def test_page_reads_the_chat_stream_in_parts() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    assert 'fetch("/api/chat"' in script
    assert 'method: "POST"' in script
    assert "getReader()" in script
    assert "new TextDecoder()" in script
    assert "stream: true" in script
    assert r'split("\n")' in script


def test_page_only_appends_answer_text() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    assert "appendData(" in script
    # Fixed texts are looked up by key, never written into the script.
    for key in ("personal-info-reminder", "error"):
        assert f'texts["{key}"]' in script


def test_page_cancels_the_stream_when_reading_stops_early() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    assert "} finally {" in script
    assert "reader.cancel().catch(" in script


def test_messages_are_busy_while_answering() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    assert 'messages.setAttribute("aria-busy", value ? "true" : "false")' in script


def test_page_keeps_the_question_when_it_is_not_answered() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    # Only a typed question clears the field; an example tap keeps the draft.
    assert "if (fromField) {" in script
    assert "ask(example.text, false)" in script
    assert "ask(question.value, true)" in script
    # Any failure puts the question back into an empty field.
    assert "if (!answered && !question.value) {" in script
    assert "question.value = text;" in script


def test_source_links_open_in_a_new_tab_safely() -> None:
    script = (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")

    assert 'target = "_blank"' in script
    assert 'rel = "noopener"' in script


def _app_js() -> str:
    return (Path(STATIC_DIR) / "app.js").read_text(encoding="utf-8")


def _history_js() -> str:
    return (Path(STATIC_DIR) / "history.js").read_text(encoding="utf-8")


def _html() -> str:
    return (Path(STATIC_DIR) / "index.html").read_text(encoding="utf-8")


def test_history_script_is_served_and_loaded_before_the_page_script(client: TestClient) -> None:
    html = _html()

    assert client.get("/history.js").status_code == 200
    assert '<script src="/history.js" defer></script>' in html
    assert html.index('src="/history.js"') < html.index('src="/app.js"')


def test_saved_chats_live_on_the_device_and_the_open_one_in_the_tab() -> None:
    js = _app_js()
    history = _history_js()

    # Saved chats in localStorage (AD-3); the open chat's id in this tab's sessionStorage.
    assert 'const LIST_KEY = "conversations";' in history
    assert 'const OPEN_KEY = "open-conversation";' in history
    assert 'storage("localStorage")' in js
    assert 'storage("sessionStorage")' in js
    # Storage is only touched through history.js, which takes the storage objects.
    assert "localStorage." not in js and "sessionStorage." not in js
    assert "localStorage." not in history and "sessionStorage." not in history
    assert "window." not in history
    # Migrate, then open this tab's chat (tested in tests/test_history_js.py).
    assert "current = Chats.startOpen(local, session, Chats.createId(), Date.now());" in js


def test_page_stores_the_clean_question_and_shown_text_only_after_done() -> None:
    js = _app_js()

    assert "record.answer += event.delta;" in js
    assert (
        "if (answered && record.question.trim() && record.answer.trim()) {\n        storeExchange(record);"
        in js
    )
    assert 'return event.type === "done";' in js
    # Append, save and mark open in one tested step (tests/test_history_js.py).
    assert (
        "current = Chats.appendExchange(local, session, current, record, Date.now(), Chats.createId(), "
        "feedbackMemory);" in js
    )


def test_page_sends_at_most_ten_exchanges_of_the_open_chat_as_question_and_answer() -> None:
    js = _app_js()
    history = _history_js()

    assert ".slice(-MAX_HISTORY)" in history
    assert "return { question: entry.question, answer: entry.answer };" in history
    # Only the chat on screen is sent, never the saved list.
    assert "history: Chats.historyToSend(current.exchanges)" in js


def test_page_shows_the_open_conversation() -> None:
    js = _app_js()

    assert "showConversation();" in js
    assert "for (const entry of current.exchanges)" in js


def test_page_history_limits_match_the_server() -> None:
    from app.web import chat

    history = _history_js()

    assert f"const MAX_HISTORY = {chat.MAX_HISTORY_ITEMS};" in history
    assert f"const MAX_QUESTION_CHARS = {chat.MAX_QUESTION_CHARS};" in history
    assert f"const MAX_ANSWER_CHARS = {chat.MAX_ANSWER_CHARS};" in history
    # Turns over the limits are left out, so one long turn cannot block later questions.
    assert "entry.answer.trim().length <= MAX_ANSWER_CHARS" in history
    assert "const MAX_CONVERSATIONS = 20;" in history
    assert "const MAX_STORED = 50;" in history


def test_page_stores_only_the_clean_question() -> None:
    js = _app_js()

    assert 'const record = { question: "", answer: "", sources: [], reminder: false };' in js
    assert 'typeof event.clean_question === "string" ? event.clean_question : ""' in js


def test_page_has_the_top_bar_and_the_history_panel() -> None:
    html = _html()

    for element_id in (
        "top-bar",
        "history-button",
        "new-chat-button",
        "history-panel",
        "history-title",
        "history-close",
        "history-list",
        "history-empty",
        "delete-all-chats",
    ):
        assert f'id="{element_id}"' in html, element_id
    assert 'role="dialog"' in html and 'aria-modal="true"' in html


def test_page_labels_come_from_the_texts_api() -> None:
    js = _app_js()

    for key in (
        "history-button",
        "new-chat-button",
        "history-title",
        "history-close",
        "history-empty",
        "delete-all-chats",
        "delete-chat",
    ):
        assert f'texts["{key}"]' in js, key


def test_deleting_asks_first_with_a_fixed_text() -> None:
    js = _app_js()

    assert '!window.confirm(texts["confirm-delete-chat"])' in js
    assert '!window.confirm(texts["confirm-delete-all-chats"])' in js
    # Deleting the open chat, or all chats, leaves an empty new chat.
    assert "if (id === current.id) {\n      showChat(emptyChat());" in js
    assert "Chats.deleteAll(local);\n    showChat(emptyChat());" in js


def test_new_chat_and_history_are_disabled_while_answering_or_sending_feedback() -> None:
    js = _app_js()

    assert "newChatButton.disabled = value;" in js
    assert "historyButton.disabled = value;" in js
    assert 'for (const button of historyPanel.querySelectorAll("button"))' in js
    assert "return answering || sendingFeedback;" in js.split("function busy(")[1].split("\n  }\n")[0]
    for name in ("ask", "startNewChat", "openHistory", "reopenChat", "deleteChat", "deleteAllChats"):
        body = js.split(f"function {name}(")[1].split("\n  }\n")[0]
        assert "busy()" in body, name


def test_page_behind_the_panel_is_inert_while_it_is_open() -> None:
    js = _app_js()

    assert (
        'const behindPanel = [document.querySelector("header.top"), document.querySelector("main"), form];'
        in js
    )
    assert 'element.toggleAttribute("inert", value);' in js
    open_body = js.split("function openHistory(")[1].split("\n  }\n")[0]
    close_body = js.split("function closeHistory(")[1].split("\n  }\n")[0]
    assert "setBehindPanelInert(true);" in open_body
    # Inert is removed before focus goes back to the history button.
    assert close_body.index("setBehindPanelInert(false);") < close_body.index("historyButton.focus();")


def test_reopening_a_deleted_chat_keeps_the_panel_open() -> None:
    body = _app_js().split("function reopenChat(")[1].split("\n  }\n")[0]

    assert body.index("if (!stored) {") < body.index("closeHistory();")
    assert "renderHistoryList();" in body.split("if (!stored) {")[1].split("return;")[0]


def test_history_panel_fits_narrow_screens() -> None:
    css = (Path(STATIC_DIR) / "style.css").read_text(encoding="utf-8")

    panel = css.split(".history-panel {")[1].split("}")[0]
    assert "position: fixed;" in panel and "overflow-x: hidden;" in panel
    # The question shrinks next to the delete button instead of widening the row.
    assert "min-width: 0;" in css.split(".history-open {")[1].split("}")[0]
    for rule in (".top-button {", ".history-open {", ".history-delete,\n.delete-all {"):
        assert "min-height: 48px;" in css.split(rule)[1].split("}")[0], rule


# --- Feedback question (Story 2.3) -------------------------------------------------------


def test_feedback_buttons_come_only_after_a_finished_done_reply() -> None:
    js = _app_js()

    assert 'info.category = typeof event.category === "string" ? event.category : null;' in js
    assert "if (Chats.showsFeedback(info.category, answered)) {\n        reply.feedback();" in js
    # A replayed chat (reload, reopen) shows the question text without buttons.
    replay = js.split("function showConversation(")[1].split("\n  }\n")[0]
    assert "feedback" not in replay
    # The category is never stored with the exchange.
    assert 'const record = { question: "", answer: "", sources: [], reminder: false };' in js


def test_feedback_texts_and_button_labels_come_from_the_texts_api() -> None:
    js = _app_js()

    assert 'texts["feedback-question"]' in js
    assert 'texts["feedback-" + answer]' in js and 'for (const answer of ["yes", "no"])' in js
    # The follow-up and thanks keys come from history.js (tested in Node).
    assert "texts[result.textKey]" in js
    history = _history_js()
    assert '"feedback-follow-up"' in history and '"feedback-thanks"' in history


def test_feedback_is_posted_with_the_id_and_answer_only() -> None:
    js = _app_js()

    body = js.split("async function sendFeedback(")[1].split("\n  }\n")[0]
    assert 'fetch("/api/feedback"' in body
    assert 'method: "POST"' in body
    assert "body: JSON.stringify(Chats.feedbackBody(id, answer))," in body
    # One tap is one row: disabled before the request; back on failure with the error text.
    assert body.index("button.disabled = true;") < body.index('fetch("/api/feedback"')
    assert "if (response.status !== 204) {" in body
    assert 'note.textContent = texts["error"];' in body
    assert 'group.dataset.state = "open";' in body.split("} catch (error) {")[1]


def test_yes_ends_the_chat_and_the_next_question_starts_a_new_one() -> None:
    js = _app_js()

    end = js.split("function endChat(")[1].split("\n  }\n")[0]
    assert "chatEnded = true;" in end
    assert "Chats.dropConversationId(session, feedbackMemory);" in end
    assert "Chats.setOpenId(session, null);" in end
    ask = js.split("async function ask(")[1].split("\n  }\n")[0]
    assert "if (chatEnded) {" in ask and "showChat(emptyChat());" in ask
    # The id is made at the first question of a chat, before the request.
    assert ask.index("Chats.conversationId(session, feedbackMemory, newConversationId);") < ask.index(
        "setAnswering(true);"
    )


def test_new_chat_and_reopen_drop_the_conversation_id() -> None:
    js = _app_js()

    show = js.split("function showChat(")[1].split("\n  }\n")[0]
    assert "Chats.dropConversationId(session, feedbackMemory);" in show
    assert "chatEnded = false;" in show
    for name in ("startNewChat", "reopenChat"):
        assert "showChat(" in js.split(f"function {name}(")[1].split("\n  }\n")[0], name


def test_conversation_id_lives_in_session_storage_only() -> None:
    history = _history_js()
    js = _app_js()

    assert 'const CONVERSATION_ID_KEY = "conversation-id";' in history
    assert "Chats.uuid4(window.crypto)" in js
    # Only history.js touches the storage and builds the body; the page never stores the id.
    assert "conversation-id" not in js and "conversation_id:" not in js
    assert "return { conversation_id: id, answer: answer };" in history


def test_open_feedback_buttons_are_disabled_while_busy() -> None:
    js = _app_js()

    body = js.split("function setControlsDisabled(")[1].split("\n  }\n")[0]
    assert (
        "for (const button of messages.querySelectorAll('.feedback[data-state=\"open\"] button')) {" in body
    )
    for name in ("setAnswering", "setSendingFeedback"):
        assert "setControlsDisabled(busy());" in js.split(f"function {name}(")[1].split("\n  }\n")[0], name


def test_a_feedback_request_blocks_everything_else_and_a_late_result_is_ignored() -> None:
    body = _app_js().split("async function sendFeedback(")[1].split("\n  }\n")[0]

    assert 'if (group.dataset.state !== "open" || busy()) {' in body
    assert body.index("setSendingFeedback(true);") < body.index('fetch("/api/feedback"')
    assert body.index('fetch("/api/feedback"') < body.index("setSendingFeedback(false);")
    # A group closed meanwhile (e.g. by "Yes") ignores the result.
    after = body.split("setSendingFeedback(false);")[1]
    assert after.lstrip().startswith('if (group.dataset.state !== "sending") {')


def test_only_the_latest_feedback_question_can_be_answered() -> None:
    js = _app_js()

    close = js.split("function closeFeedbackGroups(")[1].split("\n  }\n")[0]
    # Open and sending groups both close.
    assert "messages.querySelectorAll('.feedback:not([data-state=\"closed\"])')" in close
    assert 'group.dataset.state = "closed";' in close
    add = js.split("function addFeedbackButtons(")[1].split("\n  }\n")[0]
    assert add.index("closeFeedbackGroups();") < add.index('group.dataset.state = "open";')
    assert "closeFeedbackGroups();" in js.split("function endChat(")[1].split("\n  }\n")[0]


def test_feedback_buttons_are_actions_not_toggles() -> None:
    js = _app_js()
    css = (Path(STATIC_DIR) / "style.css").read_text(encoding="utf-8")

    assert "aria-pressed" not in js and "aria-pressed" not in css
    assert 'button.classList.add("feedback-chosen");' in js
    assert 'button.setAttribute("aria-current", "true");' in js
    assert ".feedback-button.feedback-chosen {" in css
    # The text after an answer is announced.
    assert 'note.setAttribute("role", "status");' in js


def test_feedback_buttons_fit_narrow_screens_and_are_large_enough() -> None:
    css = (Path(STATIC_DIR) / "style.css").read_text(encoding="utf-8")

    group = css.split(".feedback {")[1].split("}")[0]
    assert "display: flex;" in group and "flex-wrap: wrap;" in group
    button = css.split(".feedback-button {")[1].split("}")[0]
    assert "min-height: 48px;" in button and "min-width: 48px;" in button
    assert "max-width: 100%;" in button
