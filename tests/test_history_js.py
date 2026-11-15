"""Saved chats on the device: runs app/static/history.js in Node with an in-memory storage.

There is no browser test runner (Playwright is deferred), so the storage logic is kept
as pure functions in history.js and checked here. Each test is one row of the I/O matrix
in docs/implementation/spec-chat-history-and-new-chat.md.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.main import STATIC_DIR

NODE = shutil.which("node")
HISTORY_JS = Path(STATIC_DIR) / "history.js"

# Skipped locally without Node; in CI (`CI` set) a missing node fails instead of
# silently dropping the only runtime checks of the storage logic.
pytestmark = pytest.mark.skipif(NODE is None and not os.environ.get("CI"), reason="node is not on PATH")

PRELUDE = r"""
const H = require(process.argv[1]);
function memory(initial) {
  const data = Object.assign({}, initial || {});
  return {
    data: data,
    getItem: function (key) {
      return Object.prototype.hasOwnProperty.call(data, key) ? data[key] : null;
    },
    setItem: function (key, value) { data[key] = String(value); },
    removeItem: function (key) { delete data[key]; },
  };
}
function full(initial) {
  const storage = memory(initial);
  storage.setItem = function () { throw new Error("QuotaExceededError"); };
  return storage;
}
function blocked() {
  const fail = function () { throw new Error("SecurityError"); };
  return { getItem: fail, setItem: fail, removeItem: fail };
}
function ex(n) {
  return {
    question: "q" + n,
    answer: "a" + n,
    sources: [{ title: "t" + n, url: "https://example.org/" + n }],
    reminder: n % 2 === 0,
  };
}
function exchanges(count) {
  const list = [];
  for (let n = 1; n <= count; n += 1) list.push(ex(n));
  return list;
}
function ids(local) {
  return H.loadList(local).map(function (c) { return c.id; });
}
"""


def run(body: str) -> object:
    """Runs `body` (a JS function body that returns a JSON value) after PRELUDE."""
    script = (
        PRELUDE
        + "\nconst result = (function () {\n"
        + body
        + "\n})();\nprocess.stdout.write(JSON.stringify(result === undefined ? null : result));\n"
    )
    assert NODE is not None, "node is not on PATH; it is required in CI"
    done = subprocess.run(
        [NODE, "-e", script, str(HISTORY_JS)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_history_js_uses_the_server_limits() -> None:
    from app.web import chat

    assert run("return [H.MAX_HISTORY, H.MAX_STORED, H.MAX_CONVERSATIONS];") == [
        chat.MAX_HISTORY_ITEMS,
        50,
        20,
    ]


def test_first_question_saves_a_new_conversation_first_in_the_list() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "old", exchanges: [ex(1)] }, 1000);
        const ok = H.saveConversation(local, { id: "new", exchanges: [ex(2)] }, 2000);
        return { ok: ok, list: H.loadList(local) };
    """)

    assert result["ok"] is True
    first = result["list"][0]
    assert first["id"] == "new"
    assert first["updated"] == 2000
    assert first["exchanges"] == [
        {
            "question": "q2",
            "answer": "a2",
            "sources": [{"title": "t2", "url": "https://example.org/2"}],
            "reminder": True,
        }
    ]
    assert [c["id"] for c in result["list"]] == ["new", "old"]


# A full storage can still delete; a blocked one cannot do anything.
@pytest.mark.parametrize(("storage", "deleted"), [("full()", True), ("blocked()", False)])
def test_storage_full_or_blocked_saves_nothing_and_does_not_throw(storage: str, deleted: bool) -> None:
    result = run(f"""
        const local = {storage};
        return {{
          saved: H.saveConversation(local, {{ id: "a", exchanges: [ex(1)] }}, 1),
          list: H.loadList(local),
          deleted: H.deleteAll(local),
        }};
    """)

    assert result == {"saved": False, "list": [], "deleted": deleted}


def test_follow_up_appends_and_moves_the_conversation_to_the_top() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.saveConversation(local, { id: "b", exchanges: [ex(2)] }, 2);
        H.saveConversation(local, { id: "a", exchanges: [ex(1), ex(3)] }, 3);
        const list = H.loadList(local);
        return { ids: ids(local), questions: list[0].exchanges.map(function (e) { return e.question; }) };
    """)

    assert result == {"ids": ["a", "b"], "questions": ["q1", "q3"]}


def test_a_conversation_keeps_at_most_fifty_exchanges() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: exchanges(55) }, 1);
        const saved = H.loadList(local)[0].exchanges;
        return [saved.length, saved[0].question];
    """)

    assert result == [50, "q6"]


def test_new_chat_and_error_turn_add_no_list_item() -> None:
    # An empty chat (nothing stored after `done`) is never saved; the list stays as it was.
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        const before = local.getItem(H.LIST_KEY);
        const savedEmpty = H.saveConversation(local, { id: "b", exchanges: [] }, 2);
        const savedNoId = H.saveConversation(local, { id: null, exchanges: [ex(2)] }, 3);
        return [savedEmpty, savedNoId, local.getItem(H.LIST_KEY) === before];
    """)

    assert result == [False, False, True]


def test_reopen_gives_exchanges_with_sources_and_reminder_and_sends_the_last_ten() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: exchanges(12) }, 1);
        H.saveConversation(local, { id: "b", exchanges: [ex(99)] }, 2);
        const reopened = H.findConversation(local, "a");
        return {
          count: reopened.exchanges.length,
          last: reopened.exchanges[11],
          history: H.historyToSend(reopened.exchanges),
          missing: H.findConversation(local, "gone"),
        };
    """)

    assert result["count"] == 12
    assert result["last"]["sources"] == [{"title": "t12", "url": "https://example.org/12"}]
    assert result["last"]["reminder"] is True
    assert result["history"] == [{"question": f"q{n}", "answer": f"a{n}"} for n in range(3, 13)]
    assert result["missing"] is None


def test_history_to_send_leaves_out_turns_over_the_server_limits() -> None:
    result = run("""
        const long = { question: "q", answer: "x".repeat(10001) };
        const longQuestion = { question: "x".repeat(1001), answer: "a" };
        const fine = { question: " q ", answer: "a", sources: [], reminder: true };
        const atLimit = { question: "q".repeat(1000), answer: "a".repeat(10000) };
        return H.historyToSend([long, longQuestion, fine, { question: "", answer: "a" }, atLimit]).map(
          function (e) { return [e.question.length, e.answer.length]; }
        );
    """)

    # Exactly at the limits (1000-char question, 10000-char answer) is still sent.
    assert result == [[3, 1], [1000, 10000]]


def test_reload_keeps_the_open_conversation() -> None:
    result = run("""
        const local = memory();
        const session = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.saveConversation(local, { id: "b", exchanges: [ex(2)] }, 2);
        H.setOpenId(session, "a");
        return H.openConversation(local, session).id;
    """)

    assert result == "a"


def test_fresh_visit_opens_an_empty_chat_and_keeps_the_list() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        const freshTab = memory();
        return { open: H.openConversation(local, freshTab), ids: ids(local) };
    """)

    assert result == {"open": None, "ids": ["a"]}


def test_open_id_of_a_deleted_conversation_gives_an_empty_chat() -> None:
    result = run("""
        const local = memory();
        const session = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.setOpenId(session, "a");
        H.deleteConversation(local, "a");
        return [H.openConversation(local, session), session.getItem(H.OPEN_KEY)];
    """)

    assert result == [None, None]


def test_blocked_session_storage_opens_an_empty_chat() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.setOpenId(blocked(), "a");
        return [H.openConversation(local, blocked()), H.migrate(local, blocked(), "x", 1)];
    """)

    assert result == [None, None]


def test_old_session_conversation_is_moved_into_the_list_once() -> None:
    result = run("""
        const local = memory();
        const old = [ex(1), { question: "", answer: "x" }, ex(2)];
        const session = memory({ conversation: JSON.stringify(old) });
        const moved = H.migrate(local, session, "m", 5);
        const again = H.migrate(local, session, "n", 6);
        return {
          moved: moved,
          again: again,
          old: session.getItem(H.OLD_KEY),
          open: H.openConversation(local, session).id,
          list: H.loadList(local).map(function (c) {
            return [c.id, c.updated, c.exchanges.map(function (e) { return e.question; })];
          }),
        };
    """)

    assert result == {
        "moved": "m",
        "again": None,
        "old": None,
        "open": "m",
        "list": [["m", 5, ["q1", "q2"]]],
    }


@pytest.mark.parametrize("old", ["{not json", '{"question": "q"}', "[]", '[{"question": 1, "answer": "a"}]'])
def test_malformed_old_session_conversation_is_dropped(old: str) -> None:
    result = run(f"""
        const local = memory();
        const session = memory({{ conversation: {json.dumps(old)} }});
        return [H.migrate(local, session, "m", 1), session.getItem(H.OLD_KEY), local.getItem(H.LIST_KEY)];
    """)

    assert result == [None, None, None]


def test_old_conversation_stays_when_the_list_is_full() -> None:
    result = run("""
        const local = full();
        const session = memory({ conversation: JSON.stringify([ex(1)]) });
        return [H.migrate(local, session, "m", 1), session.getItem(H.OLD_KEY) !== null];
    """)

    assert result == [None, True]


@pytest.mark.parametrize(
    "stored",
    ["{broken", '"text"', "{}", "null", "42"],
)
def test_unreadable_list_gives_no_saved_chats(stored: str) -> None:
    result = run(f"""
        const local = memory({{ conversations: {json.dumps(stored)} }});
        return H.loadList(local);
    """)

    assert result == []


def test_malformed_entries_are_skipped_and_the_rest_shown() -> None:
    result = run("""
        const good = { id: "good", updated: 3, exchanges: [ex(1), { question: "q" }, null] };
        const older = { id: "older", updated: 1, exchanges: [ex(2)] };
        const bad = [
          null,
          "text",
          { id: "", updated: 2, exchanges: [ex(1)] },
          { id: 7, updated: 2, exchanges: [ex(1)] },
          { id: "no-time", exchanges: [ex(1)] },
          { id: "nan", updated: "2", exchanges: [ex(1)] },
          { id: "no-exchanges", updated: 2, exchanges: "x" },
          { id: "empty", updated: 2, exchanges: [{ question: " ", answer: "a" }] },
          { id: "good", updated: 0, exchanges: [ex(5)] },
        ];
        const local = memory({ conversations: JSON.stringify([older].concat(bad, [good])) });
        return H.loadList(local).map(function (c) { return [c.id, c.exchanges.length]; });
    """)

    assert result == [["good", 1], ["older", 1]]


def test_a_twenty_first_chat_drops_the_oldest_by_last_activity() -> None:
    result = run("""
        const local = memory();
        for (let n = 1; n <= 20; n += 1) {
          H.saveConversation(local, { id: "c" + n, exchanges: [ex(n)] }, n);
        }
        // c1 is the oldest by creation, but a follow-up made it recent again.
        H.saveConversation(local, { id: "c1", exchanges: [ex(1), ex(2)] }, 21);
        H.saveConversation(local, { id: "c21", exchanges: [ex(21)] }, 22);
        const list = ids(local);
        return { count: list.length, first: list.slice(0, 2), hasC1: list.includes("c1"),
                 hasC2: list.includes("c2"), stored: JSON.parse(local.getItem(H.LIST_KEY)).length };
    """)

    assert result == {"count": 20, "first": ["c21", "c1"], "hasC1": True, "hasC2": False, "stored": 20}


def test_delete_one_removes_it_from_list_and_storage() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.saveConversation(local, { id: "b", exchanges: [ex(2)] }, 2);
        const ok = H.deleteConversation(local, "a");
        const unknown = H.deleteConversation(local, "nope");
        return { ok: ok, unknown: unknown, ids: ids(local),
                 raw: JSON.parse(local.getItem(H.LIST_KEY)).map(function (c) { return c.id; }) };
    """)

    assert result == {"ok": True, "unknown": True, "ids": ["b"], "raw": ["b"]}


def test_deleting_the_last_chat_removes_the_storage_key() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.deleteConversation(local, "a");
        return local.getItem(H.LIST_KEY);
    """)

    assert result is None


def test_delete_all_removes_the_storage_key() -> None:
    result = run("""
        const local = memory({ "checklist:tourism": "[]" });
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.saveConversation(local, { id: "b", exchanges: [ex(2)] }, 2);
        const ok = H.deleteAll(local);
        return { ok: ok, list: H.loadList(local), keys: Object.keys(local.data) };
    """)

    # Only the saved chats go; other data on the device stays.
    assert result == {"ok": True, "list": [], "keys": ["checklist:tourism"]}


def test_other_tab_keeps_its_own_open_chat_and_its_saves_are_not_lost() -> None:
    result = run("""
        const local = memory();
        const tabA = memory();
        const tabB = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        H.setOpenId(tabA, "a");
        // Tab B shows the list, then tab A saves a follow-up, then tab B saves its own chat.
        const seenByB = ids(local);
        H.saveConversation(local, { id: "a", exchanges: [ex(1), ex(2)] }, 2);
        H.saveConversation(local, { id: "b", exchanges: [ex(3)] }, 3);
        H.setOpenId(tabB, "b");
        return {
          seenByB: seenByB,
          ids: ids(local),
          aLength: H.findConversation(local, "a").exchanges.length,
          openA: H.openConversation(local, tabA).id,
          openB: H.openConversation(local, tabB).id,
        };
    """)

    assert result == {"seenByB": ["a"], "ids": ["b", "a"], "aLength": 2, "openA": "a", "openB": "b"}


def test_shorten_cuts_long_questions_by_whole_characters() -> None:
    result = run("""
        return [
          H.shorten("short  question\\n", 80),
          H.shorten("abcdefghij", 5),
          Array.from(H.shorten("\\u{1F600}".repeat(10), 4)).length,
        ];
    """)

    assert result == ["short question", "abcd…", 4]


def test_ids_are_unique_strings() -> None:
    result = run("""
        const seen = new Set();
        for (let i = 0; i < 1000; i += 1) seen.add(H.createId());
        return [seen.size, typeof H.createId()];
    """)

    assert result == [1000, "string"]


def test_append_keeps_earlier_exchanges_saves_and_marks_the_chat_open() -> None:
    result = run("""
        const local = memory();
        const session = memory();
        const first = H.appendExchange(local, session, { id: null, exchanges: [] }, ex(1), 1, "a");
        const second = H.appendExchange(local, session, first, ex(2), 2, "unused");
        return {
          first: first,
          second: [second.id, second.exchanges.map(function (e) { return e.question; })],
          saved: H.findConversation(local, "a").exchanges.length,
          open: session.getItem(H.OPEN_KEY),
        };
    """)

    assert result["first"]["id"] == "a"
    assert result["second"] == ["a", ["q1", "q2"]]
    assert result["saved"] == 2
    assert result["open"] == "a"


def test_append_caps_the_open_chat_at_fifty_exchanges() -> None:
    result = run("""
        const local = memory();
        const full50 = { id: null, exchanges: exchanges(50) };
        const chat = H.appendExchange(local, memory(), full50, ex(51), 1, "a");
        const saved = H.findConversation(local, "a");
        return [chat.exchanges.length, chat.exchanges[0].question, saved.exchanges.length];
    """)

    assert result == [50, "q2", 50]


def test_append_with_storage_full_keeps_the_chat_in_memory_without_an_id() -> None:
    result = run("""
        const session = memory();
        const chat = H.appendExchange(full(), session, { id: null, exchanges: [ex(1)] }, ex(2), 1, "a");
        const sent = H.historyToSend(chat.exchanges).length;
        return [chat.id, chat.exchanges.length, session.getItem(H.OPEN_KEY), sent];
    """)

    # Not saved: no id, no open id, but the follow-up still sends both exchanges.
    assert result == [None, 2, None, 2]


@pytest.mark.parametrize("delete", ['H.deleteConversation(local, "a")', "H.deleteAll(local)"])
def test_chat_deleted_in_another_tab_is_not_brought_back_by_a_follow_up(delete: str) -> None:
    result = run(f"""
        const local = memory();
        const tabA = memory();
        let chat = H.appendExchange(local, tabA, {{ id: null, exchanges: [] }}, ex(1), 1, "a");
        chat = H.appendExchange(local, tabA, chat, ex(2), 2, "unused");
        {delete};  // in tab B
        chat = H.appendExchange(local, tabA, chat, ex(3), 3, "b");
        return {{
          chat: [chat.id, chat.exchanges.map(function (e) {{ return e.question; }})],
          ids: ids(local),
          open: tabA.getItem(H.OPEN_KEY),
        }};
    """)

    # The deleted exchanges stay deleted; the follow-up starts a new chat.
    assert result == {"chat": ["b", ["q3"]], "ids": ["b"], "open": "b"}


def test_start_open_migrates_old_data_before_opening() -> None:
    result = run("""
        const local = memory();
        const session = memory({ conversation: JSON.stringify([ex(1)]) });
        const chat = H.startOpen(local, session, "m", 5);
        return { chat: [chat.id, chat.exchanges.length], old: session.getItem(H.OLD_KEY), ids: ids(local) };
    """)

    assert result == {"chat": ["m", 1], "old": None, "ids": ["m"]}


def test_start_open_reopens_the_tabs_chat_or_gives_an_empty_one() -> None:
    result = run("""
        const local = memory();
        H.saveConversation(local, { id: "a", exchanges: [ex(1)] }, 1);
        const reload = memory();
        H.setOpenId(reload, "a");
        return [H.startOpen(local, reload, "x", 2).id, H.startOpen(local, memory(), "y", 2)];
    """)

    assert result == ["a", {"id": None, "exchanges": []}]
