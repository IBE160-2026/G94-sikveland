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


# --- Document checklist (Story 3.2) ------------------------------------------------------


def _checklist_js() -> str:
    return (Path(STATIC_DIR) / "checklist.js").read_text(encoding="utf-8")


def _css() -> str:
    return (Path(STATIC_DIR) / "style.css").read_text(encoding="utf-8")


def _body(js: str, name: str) -> str:
    return js.split(f"function {name}(")[1].split("\n  }\n")[0]


def test_checklist_script_is_served_and_loaded_before_the_page_script(client: TestClient) -> None:
    html = _html()

    assert client.get("/checklist.js").status_code == 200
    assert '<script src="/checklist.js" defer></script>' in html
    assert html.index('src="/checklist.js"') < html.index('src="/app.js"')
    assert "const Lists = window.Checklist;" in _app_js()


def test_page_has_the_checklist_button_and_view() -> None:
    html = _html()

    top_bar = html.split('id="top-bar"')[1].split("</nav>")[0]
    assert 'id="checklist-button"' in top_bar and 'aria-controls="checklist-panel"' in top_bar
    panel = html.split('id="checklist-panel"')[1].split("</section>")[0]
    assert 'role="dialog" aria-modal="true"' in panel and 'aria-labelledby="checklist-title"' in panel
    for element_id in (
        "checklist-title",
        "checklist-close",
        "checklist-choose-purpose",
        "checklist-purposes",
        "checklist-view",
        "checklist-purpose-name",
        "checklist-change-purpose",
        "checklist-loading",
        "checklist-progress",
        "checklist-all-done",
        "checklist-items",
        "checklist-failed",
        "checklist-error",
        "checklist-retry",
    ):
        assert f'id="{element_id}"' in panel, element_id
    # The progress and all-done text are announced.
    assert 'id="checklist-status" class="checklist-status" role="status"' in panel


def test_checklist_labels_come_from_the_texts_api() -> None:
    js = _app_js()

    for key in (
        "checklist-button",
        "checklist-title",
        "checklist-back",
        "checklist-choose-purpose",
        "checklist-change-purpose",
        "checklist-not-applicable",
        "checklist-progress",
        "checklist-all-done",
        "checklist-loading",
        "checklist-retry",
        "error",
    ):
        assert f'texts["{key}"]' in js, key
    # The retry button holds only a symbol; its name comes from the texts.
    assert 'checklistRetry.setAttribute("aria-label", data.texts["checklist-retry"]);' in js
    # The three purpose names: one key per purpose, in the order of checklist.js.
    assert 'data.texts["checklist-purpose-" + purpose]' in js
    assert 'texts["checklist-purpose-" + purpose]' in _body(js, "choosePurpose")
    assert "for (const purpose of Lists.PURPOSES) {" in js


def test_checklist_button_stays_usable_while_busy() -> None:
    js = _app_js()

    assert "checklistButton" not in _body(js, "setControlsDisabled")
    for name in ("openChecklist", "closeChecklist", "choosePurpose", "changeChecklist", "changePurpose"):
        assert "busy()" not in _body(js, name), name


def test_checklist_view_is_a_full_screen_dialog_like_the_saved_chats() -> None:
    js = _app_js()

    open_body = _body(js, "openChecklist")
    close_body = _body(js, "closeChecklist")
    assert "setBehindPanelInert(true);" in open_body and "checklistPanel.hidden = false;" in open_body
    assert "checklistClose.focus();" in open_body
    # Inert is removed before focus goes back to the Checklist button.
    assert close_body.index("setBehindPanelInert(false);") < close_body.index("checklistButton.focus();")
    # Opening always starts with the purpose choice.
    assert "showPurposeChoice();" in open_body
    assert "checklistChoice.hidden = false;" in _body(js, "showPurposeChoice")
    assert "showPurposeChoice();" in _body(js, "changePurpose")
    # Back and Escape close it.
    assert 'checklistClose.addEventListener("click", closeChecklist);' in js
    assert 'checklistChangePurpose.addEventListener("click", changePurpose);' in js
    # Escape on the document, so it also works when focus fell to the page body.
    escape = js.split('document.addEventListener("keydown", function (event) {')[1].split("});")[0]
    assert 'event.key === "Escape" && !checklistPanel.hidden' in escape and "closeChecklist();" in escape


def test_focus_goes_to_the_heading_when_the_focused_retry_button_is_hidden() -> None:
    body = _body(_app_js(), "renderChecklist")

    assert "const retryHadFocus = checklistFailed.contains(document.activeElement);" in body
    assert body.index("retryHadFocus = ") < body.index("checklistFailed.hidden = true;")
    assert "if (retryHadFocus) {\n      checklistPurposeName.focus();" in body


def test_a_loading_text_shows_until_the_items_or_the_error_appear() -> None:
    js = _app_js()

    load = _body(js, "loadChecklist")
    assert load.index("checklistLoading.hidden = false;") < load.index('fetch("/api/checklists/')
    assert load.index('fetch("/api/checklists/') < load.index("checklistLoading.hidden = true;")
    assert load.index("checklistLoading.hidden = true;") < load.index("if (failed) {")
    assert 'id="checklist-loading" class="checklist-loading" hidden' in _html()


def test_checklist_never_touches_the_chat() -> None:
    js = _app_js()

    for name in (
        "openChecklist",
        "closeChecklist",
        "showPurposeChoice",
        "changePurpose",
        "choosePurpose",
        "loadChecklist",
        "renderChecklist",
        "changeChecklist",
        "refreshChecklist",
    ):
        body = _body(js, name)
        for chat in ("messages", "current", "showChat", "showConversation", "Chats.", "answering", "reader"):
            assert chat not in body, (name, chat)


def test_ticks_are_saved_on_the_device_and_never_sent() -> None:
    js = _app_js()

    change = _body(js, "changeChecklist")
    assert "Lists.save(local, checklistMemory, checklistPurpose, state);" in change
    for name in ("changeChecklist", "refreshChecklist", "renderChecklist"):
        assert "fetch(" not in _body(js, name), name
    # The only checklist request is the checklist itself.
    load = _body(js, "loadChecklist")
    assert 'fetch("/api/checklists/" + purpose, { cache: "no-store" })' in load
    assert js.count('fetch("/api/checklists/') == 1
    assert "checklistState = Lists.load(local, checklistMemory, purpose, items);" in load
    # Storage keys live only in checklist.js.
    assert "checklist:" not in js and "checklist-na:" not in js
    checklist = _checklist_js()
    assert 'const TICK_PREFIX = "checklist:";' in checklist
    assert 'const NOT_APPLICABLE_PREFIX = "checklist-na:";' in checklist


def test_checklist_failure_shows_the_error_text_with_a_retry() -> None:
    js = _app_js()

    load = _body(js, "loadChecklist")
    assert "if (!response.ok) {" in load
    assert 'checklistError.textContent = texts["error"];' in load
    assert "checklistFailed.hidden = false;" in load
    # A late response for another purpose, or after closing, is ignored.
    assert "if (request !== checklistRequest) {" in load
    assert "checklistRequest += 1;" in _body(js, "closeChecklist")
    assert 'checklistRetry.addEventListener("click", loadChecklist);' in js


def test_checklist_items_have_a_tick_box_a_safe_source_link_and_doesnt_apply() -> None:
    body = _body(_app_js(), "renderChecklist")

    assert 'tick.type = "checkbox";' in body
    assert "if (item.conditional) {" in body and 'notApplicable.type = "checkbox";' in body
    assert "Lists.toggleTick(checklistState, item.id)" in body
    assert "Lists.toggleNotApplicable(checklistState, item.id)" in body
    # https only, new tab, no opener; text set as text, never as HTML.
    assert "const source = safeSources([item.source])[0];" in body
    assert 'link.target = "_blank";' in body and 'link.rel = "noopener";' in body
    assert "text.textContent = item.text;" in body
    assert "innerHTML" not in _app_js()
    # "Doesn't apply" only dims the item: its tick box stays usable, and ticking clears it.
    assert "tick.disabled" not in _app_js()
    dimmed = _css().split('.checklist-item[data-state="not-applicable"] .checklist-tick {')[1].split("}")[0]
    assert "opacity: 0.5;" in dimmed and "cursor: default;" not in dimmed


def test_checklist_progress_and_all_done() -> None:
    body = _body(_app_js(), "refreshChecklist")

    assert "const counts = Lists.progress(checklistItems, checklistState);" in body
    assert 'Lists.progressText(texts["checklist-progress"], counts)' in body
    assert "checklistAllDone.hidden = !counts.allDone;" in body


def test_checklist_view_fits_narrow_screens_and_targets_are_large_enough() -> None:
    css = _css()

    panel = css.split(".checklist-panel,\n.history-panel {")[1].split("}")[0]
    assert "position: fixed;" in panel and "overflow-x: hidden;" in panel
    for rule in (".checklist-purpose {", ".checklist-tick,\n.checklist-na {", ".checklist-source {"):
        assert "min-height: 48px;" in css.split(rule)[1].split("}")[0], rule
    # Long item texts and source titles wrap instead of widening the row.
    assert "overflow-wrap: anywhere;" in css.split("body {")[1].split("}")[0]
    for rule in (".checklist-text {", ".checklist-source {", ".checklist-item {"):
        assert "min-width: 0;" in css.split(rule)[1].split("}")[0], rule
    # The tick box is large; the "doesn't apply" box is smaller.
    assert "width: 28px;" in css.split(".checklist-box {")[1].split("}")[0]
    assert "width: 20px;" in css.split(".checklist-na-box {")[1].split("}")[0]
