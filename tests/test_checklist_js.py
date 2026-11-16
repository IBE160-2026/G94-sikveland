"""Checklist ticks on the device: runs app/static/checklist.js in Node with an in-memory storage.

There is no browser test runner (Playwright is deferred), so the tick logic is kept as
pure functions in checklist.js and checked here. Each test is one logic row of the I/O
matrix in docs/implementation/spec-3-2-tick-off-documents-and-the-ticks-are-kept.md.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

from app.main import STATIC_DIR
from app.ports.content import VISIT_PURPOSES

NODE = shutil.which("node")
CHECKLIST_JS = Path(STATIC_DIR) / "checklist.js"

# Skipped locally without Node; in CI (`CI` set) a missing node fails instead.
pytestmark = pytest.mark.skipif(NODE is None and not os.environ.get("CI"), reason="node is not on PATH")

PRELUDE = r"""
const C = require(process.argv[1]);
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
function item(id, conditional) {
  return { id: id, text: "text " + id, conditional: conditional === true,
           source: { title: "t", url: "https://example.org/" + id } };
}
// A family checklist like the served one: two items that always apply, one conditional.
const FAMILY = [item("passport"), item("photo"), item("employment-proof", true)];
function stored(local, purpose) {
  return [local.getItem(C.tickKey(purpose)), local.getItem(C.notApplicableKey(purpose))];
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
        [NODE, "-e", script, str(CHECKLIST_JS)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=30,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return json.loads(done.stdout)


def test_purposes_and_storage_keys_match_the_server() -> None:
    result = run("""
        return { purposes: C.PURPOSES, keys: [C.tickKey("family"), C.notApplicableKey("family")],
                 valid: C.PURPOSES.map(C.isPurpose),
                 invalid: ["Family", "business", "", null].map(C.isPurpose) };
    """)

    assert result["purposes"] == list(VISIT_PURPOSES)
    assert result["keys"] == ["checklist:family", "checklist-na:family"]
    assert result["valid"] == [True, True, True]
    assert result["invalid"] == [False] * 4


def test_tick_saves_the_id_list_and_updates_progress() -> None:
    result = run("""
        const local = memory();
        const mem = {};
        let state = C.load(local, mem, "family", FAMILY);
        const before = C.progress(FAMILY, state);
        state = C.toggleTick(state, "passport");
        const saved = C.save(local, mem, "family", state);
        return { saved: saved, stored: stored(local, "family"), before: before,
                 after: C.progress(FAMILY, state) };
    """)

    assert result["saved"] is True
    assert result["stored"] == ['["passport"]', "[]"]
    assert result["before"] == {"done": 0, "total": 3, "allDone": False}
    assert result["after"] == {"done": 1, "total": 3, "allDone": False}


def test_untick_removes_it_from_the_list() -> None:
    result = run("""
        const local = memory({ "checklist:family": '["passport","photo"]' });
        const mem = {};
        let state = C.load(local, mem, "family", FAMILY);
        state = C.toggleTick(state, "passport");
        C.save(local, mem, "family", state);
        return stored(local, "family")[0];
    """)

    assert json.loads(result) == ["photo"]


def test_doesnt_apply_is_stored_apart_clears_the_tick_and_drops_the_total() -> None:
    result = run("""
        const local = memory();
        const mem = {};
        let state = C.load(local, mem, "family", FAMILY);
        state = C.toggleTick(state, "employment-proof");
        state = C.toggleNotApplicable(state, "employment-proof");
        C.save(local, mem, "family", state);
        return { state: state, stored: stored(local, "family"), progress: C.progress(FAMILY, state) };
    """)

    assert result["state"] == {"ticked": [], "notApplicable": ["employment-proof"]}
    assert result["stored"] == ["[]", '["employment-proof"]']
    assert result["progress"] == {"done": 0, "total": 2, "allDone": False}


def test_ticking_an_item_marked_doesnt_apply_clears_that_choice() -> None:
    result = run("""
        let state = { ticked: [], notApplicable: ["employment-proof"] };
        return C.toggleTick(state, "employment-proof");
    """)

    # Never both: choosing one clears the other.
    assert result == {"ticked": ["employment-proof"], "notApplicable": []}


def test_undo_doesnt_apply_makes_the_item_count_again() -> None:
    result = run("""
        const local = memory();
        const mem = {};
        let state = C.toggleNotApplicable(C.load(local, mem, "family", FAMILY), "employment-proof");
        state = C.toggleNotApplicable(state, "employment-proof");
        C.save(local, mem, "family", state);
        return { stored: stored(local, "family"), progress: C.progress(FAMILY, state) };
    """)

    assert result["stored"] == ["[]", "[]"]
    assert result["progress"] == {"done": 0, "total": 3, "allDone": False}


def test_days_later_the_same_ticks_and_choices_come_back() -> None:
    result = run("""
        const local = memory();
        let state = C.load(local, {}, "family", FAMILY);
        state = C.toggleTick(state, "passport");
        state = C.toggleTick(state, "photo");
        state = C.toggleNotApplicable(state, "employment-proof");
        C.save(local, {}, "family", state);
        // A new page (browser closed and opened again): an empty memory, the same storage.
        return C.load(local, {}, "family", FAMILY);
    """)

    assert result == {"ticked": ["passport", "photo"], "notApplicable": ["employment-proof"]}


def test_content_change_keeps_known_ticks_ignores_removed_and_new_items_start_unticked() -> None:
    result = run("""
        const local = memory({
          "checklist:family": '["old-id","passport"]',
          "checklist-na:family": '["old-conditional","employment-proof"]',
        });
        const mem = {};
        const items = [item("passport"), item("new-item"), item("employment-proof", true)];
        const state = C.load(local, mem, "family", items);
        const loaded = JSON.parse(JSON.stringify(state));
        // Dropped on the next save.
        C.save(local, mem, "family", C.toggleTick(state, "new-item"));
        return { loaded: loaded, stored: stored(local, "family") };
    """)

    assert result["loaded"] == {"ticked": ["passport"], "notApplicable": ["employment-proof"]}
    assert json.loads(result["stored"][0]) == ["passport", "new-item"]
    assert json.loads(result["stored"][1]) == ["employment-proof"]


def test_doesnt_apply_is_ignored_for_an_item_that_is_no_longer_conditional() -> None:
    result = run("""
        const local = memory({ "checklist-na:family": '["employment-proof"]' });
        return C.load(local, {}, "family", [item("employment-proof", false)]);
    """)

    assert result == {"ticked": [], "notApplicable": []}


def test_an_id_stored_as_both_is_ticked() -> None:
    result = run("""
        const local = memory({ "checklist:family": '["employment-proof"]',
                               "checklist-na:family": '["employment-proof"]' });
        return C.load(local, {}, "family", FAMILY);
    """)

    assert result == {"ticked": ["employment-proof"], "notApplicable": []}


@pytest.mark.parametrize(
    "value",
    ["{bad", '"passport"', '{"0": "passport"}', "null", "42", "true", "[1, null, {}]"],
)
def test_corrupt_storage_is_treated_as_empty(value: str) -> None:
    result = run(f"""
        const local = memory({{ "checklist:family": {json.dumps(value)},
                                "checklist-na:family": {json.dumps(value)} }});
        return C.load(local, {{}}, "family", FAMILY);
    """)

    assert result == {"ticked": [], "notApplicable": []}


def test_a_list_with_some_bad_entries_keeps_the_good_ones_once() -> None:
    result = run("""
        const local = memory({ "checklist:family": '["photo", 7, null, "photo", "", "passport"]' });
        return C.load(local, {}, "family", FAMILY).ticked;
    """)

    assert result == ["photo", "passport"]


@pytest.mark.parametrize("storage", ["blocked()", "full()", "null"])
def test_blocked_or_full_storage_keeps_ticks_for_the_visit_only(storage: str) -> None:
    result = run(f"""
        const local = {storage};
        const mem = {{}};
        let state = C.load(local, mem, "family", FAMILY);
        state = C.toggleTick(state, "passport");
        state = C.toggleNotApplicable(state, "employment-proof");
        const saved = C.save(local, mem, "family", state);
        // Change purpose and back during the same visit: still ticked.
        const again = C.load(local, mem, "family", FAMILY);
        // A new visit (new memory): nothing was kept.
        const nextVisit = C.load(local, {{}}, "family", FAMILY);
        return {{ saved: saved, again: again, nextVisit: nextVisit }};
    """)

    assert result["saved"] is False
    assert result["again"] == {"ticked": ["passport"], "notApplicable": ["employment-proof"]}
    assert result["nextVisit"] == {"ticked": [], "notApplicable": []}


def test_a_later_successful_save_clears_the_visit_memory() -> None:
    result = run("""
        const local = memory();
        const mem = { family: { ticked: ["photo"], notApplicable: [] } };
        C.save(local, mem, "family", { ticked: ["passport"], notApplicable: [] });
        return { mem: mem, loaded: C.load(local, mem, "family", FAMILY) };
    """)

    assert result == {"mem": {}, "loaded": {"ticked": ["passport"], "notApplicable": []}}


def test_all_done_when_every_applying_item_is_ticked() -> None:
    result = run("""
        let state = { ticked: [], notApplicable: [] };
        state = C.toggleTick(state, "passport");
        state = C.toggleTick(state, "photo");
        const almost = C.progress(FAMILY, state);
        state = C.toggleNotApplicable(state, "employment-proof");
        const done = C.progress(FAMILY, state);
        const allTicked = C.progress(FAMILY, C.toggleTick(C.toggleNotApplicable(state, "employment-proof"),
                                                         "employment-proof"));
        return [almost, done, allTicked];
    """)

    assert result == [
        {"done": 2, "total": 3, "allDone": False},
        {"done": 2, "total": 2, "allDone": True},
        {"done": 3, "total": 3, "allDone": True},
    ]


def test_nothing_applying_is_not_all_done() -> None:
    result = run("""
        let state = { ticked: [], notApplicable: [] };
        const items = [item("a", true), item("b", true)];
        state = C.toggleNotApplicable(C.toggleNotApplicable(state, "a"), "b");
        return C.progress(items, state);
    """)

    assert result == {"done": 0, "total": 0, "allDone": False}


def test_purposes_are_kept_apart() -> None:
    result = run("""
        const local = memory({ "checklist:tourism": '["photo"]' });
        const mem = {};
        let state = C.toggleTick(C.load(local, mem, "family", FAMILY), "passport");
        C.save(local, mem, "family", state);
        return {
          tourism: C.load(local, mem, "tourism", FAMILY),
          friends: C.load(local, mem, "friends", FAMILY),
          keys: Object.keys(local.data).sort(),
        };
    """)

    assert result["tourism"] == {"ticked": ["photo"], "notApplicable": []}
    assert result["friends"] == {"ticked": [], "notApplicable": []}
    assert result["keys"] == ["checklist-na:family", "checklist:family", "checklist:tourism"]


def test_progress_text_fills_in_the_counts() -> None:
    result = run("""
        return [
          C.progressText("{done} of {total} ready", { done: 12, total: 15 }),
          C.progressText("x {done} {done} / {total}", { done: 0, total: 3 }),
        ];
    """)

    assert result == ["12 of 15 ready", "x 0 0 / 3"]


def test_valid_items_keeps_well_formed_items_once() -> None:
    result = run("""
        const body = { purpose: "family", items: [
          item("passport"),
          { id: "employment-proof", text: "t", conditional: true,
            source: { title: "x", url: "https://e.org" } },
          { id: "odd-flag", text: "t", conditional: "yes" },
          { id: "passport", text: "again" },
          { id: "", text: "t" }, { id: "no-text" }, { id: 7, text: "t" }, null, "text",
        ] };
        return [C.validItems(body).map(function (i) { return [i.id, i.conditional, i.source !== null]; }),
                C.validItems(null), C.validItems({ items: "x" }), C.validItems({})];
    """)

    assert result == [
        [["passport", False, True], ["employment-proof", True, True], ["odd-flag", False, False]],
        [],
        [],
        [],
    ]


def test_valid_items_keep_the_stored_english_or_an_empty_string() -> None:
    # "Show English" in the checklist view (Story 4.1) shows `en`; nothing else is sent anywhere.
    result = run("""
        const body = { items: [
          { id: "a", text: "t", en: "Passport" },
          { id: "b", text: "t" },
          { id: "c", text: "t", en: "   " },
          { id: "d", text: "t", en: 7 },
        ] };
        return C.validItems(body).map(function (i) { return [i.id, i.en]; });
    """)

    assert result == [["a", "Passport"], ["b", ""], ["c", ""], ["d", ""]]


def test_valid_items_keeps_ids_named_like_object_properties() -> None:
    result = run("""
        const body = { items: [item("constructor"), item("toString"), item("__proto__"), item("toString")] };
        return C.validItems(body).map(function (i) { return i.id; });
    """)

    assert result == ["constructor", "toString", "__proto__"]


def test_checklist_js_never_talks_to_the_server() -> None:
    source = CHECKLIST_JS.read_text(encoding="utf-8")

    for call in ("fetch(", "XMLHttpRequest", "sendBeacon", "WebSocket", "EventSource"):
        assert call not in source, call
    assert "window." not in source
    assert "localStorage." not in source and "sessionStorage." not in source


# --- "Open checklist" under an answer (Story 3.3) ----------------------------------------
# Rows of the I/O matrix in docs/implementation/spec-3-3-open-the-checklist-from-the-chat.md.


@pytest.mark.parametrize(
    ("value", "valid"),
    [
        ('["family", "friends"]', ["family", "friends"]),
        ('["tourism", "family", "friends"]', ["tourism", "family", "friends"]),
        # Server order is kept even if stored otherwise; each purpose once.
        ('["friends", "tourism", "friends"]', ["tourism", "friends"]),
        # Unknown purposes are dropped.
        ('["visa", "family"]', ["family"]),
        ('["visa"]', []),
        ('["Family", " family", 1, null, {}]', []),
        # Not a list, or missing (a chat saved before Story 3.3).
        ('"family"', []),
        ('{"0": "family", "length": 1}', []),
        ("null", []),
        ("undefined", []),
        ("[]", []),
    ],
)
def test_valid_purposes_keeps_known_purposes_in_order_once(value: str, valid: list[str]) -> None:
    assert run(f"return C.validPurposes({value});") == valid


@pytest.mark.parametrize(
    ("value", "target"),
    [
        # One purpose: that checklist directly.
        ('["tourism"]', {"purpose": "tourism"}),
        ('["family", "visa"]', {"purpose": "family"}),
        # Several: the purpose choice first.
        ('["family", "friends"]', {"purpose": None}),
        ('["tourism", "family", "friends"]', {"purpose": None}),
        # None, or nothing usable: no button.
        ("[]", None),
        ('["visa"]', None),
        ('"tourism"', None),
        ("undefined", None),
    ],
)
def test_open_target_is_the_checklist_or_the_choice_or_no_button(value: str, target: object) -> None:
    assert run(f"return C.openTarget({value});") == target
