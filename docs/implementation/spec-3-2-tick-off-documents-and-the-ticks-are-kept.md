---
title: 'Story 3.2: Tick off documents, and the ticks are kept'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '81b4c285e9980a9a393cdbe798f7989b13a7f828'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The checklists exist on the server (Story 3.1) but the applicant cannot see them, tick off what they have, or find their ticks again days later, so they still ask the adviser to check their documents (FR6, UJ-1).

**Approach:** A "Checklist" button always visible in the top bar opens a full-screen checklist view: choose a visit purpose (tourism, visiting family, visiting friends), see that checklist from `GET /api/checklists/{purpose}` with a large tick box and the source link per item, and tick or untick. Ticks stay in `localStorage` on the device only; "back" returns to the unchanged chat.

**Decision (user, 2026-11-15):** items that only apply to some applicants get a second, smaller choice "doesn't apply to me" next to the tick box. Such items are marked `conditional: true` in `content/checklists.yaml` (served as `conditional` per item). A progress line counts only items that apply ("12 of 15 ready"), so the applicant can reach "all done".

## Boundaries & Constraints

**Always:** ticked ids in `localStorage["checklist:{purpose}"]` as a JSON list (AD-11); "doesn't apply" ids in `localStorage["checklist-na:{purpose}"]`; an item is never both (choosing one clears the other); nothing about ticks reaches the server (NFR5); on load the stored ids are intersected with the served ids (removed ids ignored, new items start unticked and applying); unreadable storage is treated as empty and never breaks the page; storage blocked → ticks work for the visit but are not kept; the view is full screen like the saved-chats panel (`role="dialog"`, Escape and the back button close it, background `inert`, focus returns to the Checklist button); the chat, its stored conversation and an answer being streamed are not touched by opening or closing the view; the Checklist button stays usable while an answer streams; touch targets ≥ 48 px, 320 px without sideways scroll (NFR1); every visible text from `/api/texts` (AD-6): new keys for the button, view title, purpose choice, the three purpose names, back, change purpose, "doesn't apply to me", the progress line (with `{done}` and `{total}` filled by the page) and all-done; Thai drafted for the user's review (NFR8); pure logic (storage keys, merge, counts, state toggles) in `app/static/history.js` or a new pure module, tested in Node; `GET /api/checklists` failure → the fixed `error` text in the view with a retry.

**Never:** no ticks or purpose choice sent to the server; no change to the chat stream or saved chats; no Thai in `app/static/`; no new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Open | tap Checklist | view with the three purpose choices | N/A |
| Choose | tap "visiting family" | family items: tick box, text, source link (new tab, safe rel); conditional items also have "doesn't apply" | fetch fails → error text + retry |
| Tick | tick `passport` | `checklist:family` = `["passport"]`; progress updates | storage full/blocked → stays ticked this visit |
| Untick | untick it | removed from the list | N/A |
| Doesn't apply | on `employment-proof` | id in `checklist-na:family`, not in ticks; progress total drops by one; tick box disabled or dimmed | N/A |
| Undo | tap "doesn't apply" again | id removed; item counts again | N/A |
| Days later | reopen browser, open family | same ticks and choices | N/A |
| Content changed | stored `["old-id","passport"]`, `old-id` removed, `new-item` added | `passport` ticked, `old-id` ignored (dropped on next save), `new-item` unticked | N/A |
| Corrupt storage | `checklist:family` = `"{bad"` or not a list | treated as empty | N/A |
| All done | every applying item ticked | all-done text shown | N/A |
| Purposes separate | tick in family | tourism and friends unchanged | N/A |
| Back | tap back / Escape | chat view exactly as before, also mid-stream | N/A |
| Change purpose | in a checklist | back to the purpose choice | N/A |

</frozen-after-approval>

## Code Map

- `content/checklists.yaml`, `app/ports/content.py` `ChecklistItem`, `app/adapters/file_content.py` `_load_checklist` -- add optional boolean `conditional` (default false; reject non-boolean); mark the "if …"/"if relevant" items (employment, self-employment, minors ×3, name change, organised tour, itinerary if several countries, sponsorship form "if the inviting person is financing", ties/"if relevant", EU/EEA pointer) — the implementer decides per item from its text.
- `app/web/checklists.py` -- add `conditional` to each served item; `tests/test_checklists.py` -- response shape changes.
- `app/static/index.html` -- Checklist button in `#top-bar` (next to `#history-button`, `#new-chat-button`), a checklist `section` modelled on `#history-panel`.
- `app/static/app.js` -- reuse the panel pattern: `openHistory`/`closeHistory`, `setBehindPanelInert`, `storage(name)`, `safeSources` (https-only links); `setControlsDisabled`/`busy()` must not disable the Checklist button; `render(data)` fills the labels.
- `app/static/history.js` (or new `app/static/checklist.js` loaded before `app.js`, exported for Node like history.js) -- pure: keys, load/validate/merge, toggle tick / doesn't-apply, progress counts.
- `app/static/style.css` -- panel and checkbox styles (≥ 48 px).
- `content/texts.yaml`, `app/ports/content.py` `REQUIRED_TEXT_KEYS` -- new keys; `{done}`/`{total}` stay literal in the served text for the page to fill; `_language` in `file_content.py` rejects any brace except `{ADVISER_CONTACT}`, so allow exactly these two placeholders for the progress key only (and test that other keys still reject them).
- Tests: `tests/test_history_js.py` style Node tests for the pure module (every matrix row that is logic), `tests/test_static.py` source checks for the wiring, `tests/test_texts_api.py` for the keys.
- Docs: README (checklist view, ticks only on the device), manual test plan (new case: phone, days-later ticks, content change), `ARCHITECTURE-SPINE.md` AD-11 (the `checklist-na:` key and `conditional`).

## Tasks & Acceptance

**Execution:**
- [x] `content/checklists.yaml`, `app/ports/content.py`, `app/adapters/file_content.py`, `app/web/checklists.py` -- `conditional` per item -- user decision
- [x] Pure checklist logic module + Node tests -- storage, merge, toggles, progress -- AD-11, NFR5
- [x] `index.html`, `app.js`, `style.css` -- button, view, purpose choice, items, back -- FR6, NFR1
- [x] `content/texts.yaml`, `app/ports/content.py` -- new keys -- AD-6, NFR8
- [x] Tests (pytest + Node) for every matrix row -- AD-13
- [x] Docs in the Code Map

**Acceptance Criteria:**
- Given any tick or "doesn't apply" change, when the network log is read, then no request was made for it.
- Given the checklist view at 320 px, when a long item text and its source title are shown, then nothing scrolls sideways.

## Implementation Notes

- Conditional items (12 ids): name-change-certificate, employment-proof, self-employment-proof, the three minor-* items, itinerary, organised-tour-voucher, ties-to-thailand, eu-eea-family-member, sponsorship-form, social-and-financial-ties. Rule, tested on the committed file: `conditional` is true exactly when the English text starts with "If ". `invitation-letter` and `proof-of-relationship` always apply.
- Pure logic in a new `app/static/checklist.js` (`window.Checklist`, loaded before `app.js`), tested in `tests/test_checklist_js.py`. The state is `{ticked, notApplicable}`; on load a tick wins over a stored "doesn't apply" for the same id, and "doesn't apply" is kept only for items still conditional. When a save fails (storage blocked or full), the state is held in an in-memory map per purpose for the visit, so changing purpose and back keeps the ticks; a later successful save clears it.
- "Doesn't apply to me" is a second, smaller checkbox (not a toggle button), because `aria-pressed` is banned in `app.js`/`style.css` by an existing test, and a checkbox is the natural on/off control; it has `aria-describedby` pointing to its item's text.
- `PAGE_PLACEHOLDERS` in `app/ports/content.py` allows `{done}` and `{total}` in `checklist-progress` only, and requires both there (each language).
- Progress "all done" is `done === total` over applying items.
- The checklist panel shares the saved-chats panel CSS through combined selectors; the sticky panel header got `z-index: 1`, since a dimmed (opacity) item row painted over it.
- At 320 px the three top-bar buttons wrap onto two rows (no sideways scroll).
- Verified in headless Edge over CDP (demo mode, 320 px): open mid-stream, fetch failure + retry, ticks and "doesn't apply" stored with no network request, purposes kept apart, Escape back to the unchanged chat with the answer finishing, browser closed and reopened with the same ticks, content change, corrupt storage, all done.

- The user approved the 13 Thai checklist labels on 2026-11-15 (NFR8), choosing ไม่ต้องใช้สำหรับฉัน for "doesn't apply to me" (`e14bc88`).

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V1 | Checklist DOM wiring in `app.js` pinned only by source text; no deferred entry | medium | pre-verified gap; no browser runner. deferred (browser tests) |
| V2 | The Story 3.1 deferred entry on conditional items stays open | low | settled by this story; old entries are not edited, so the new deferred entry says so |
| E1 | Focus drops to `<body>` after a successful retry; Escape stops working | low | the focused retry button is hidden. patched (focus to heading; Escape at document level) |
| E2 | Escape does nothing after clicking non-focusable panel text | low | same root as E1. patched |
| E3 | Save writes two keys; a quota failure on the second leaves them out of step | low | needs storage full exactly between two writes; AD-11 fixes the tick key's shape. rejected |
| E4 | Two tabs on one checklist overwrite each other | low | rare on a phone (Facebook's in-app browser has its own storage); fix adds a listener. rejected |
| E5 | `validItems` plain-object set drops ids like `constructor` | low | patched (`Set`, test) |
| E6 | All items "doesn't apply" → total 0 → all-done with nothing ticked | low | patched (`total > 0`, test) |
| B1 | Focus lost after retry | low | same as E1. patched |
| B2 | Retry button has no accessible name | low | glyph only. patched (`checklist-retry` label) |
| B3 | No loading state | low | patched (`checklist-loading`) |
| B4 | Tick box disabled while "doesn't apply"; clearing path unreachable | low | patched (tick stays enabled, only dimmed) |
| B5 | Plain-object seen set | low | same as E5. patched |
| B6 | Two-key save | low | same as E3. rejected |
| B7 | Two tabs | low | same as E4. rejected |
| B8 | No way to clear ticks; "delete all chats" leaves them | low | a feature outside the intent; ticks hold only item ids. deferred |
| B9 | All-done text overclaims; "If relevant" items can be marked not applying | medium | reads as a promise the application is complete. patched (text: ticked items, hand in with the signed embassy checklist, the embassy decides) |
| B10 | README lists the story as done during review | low | same practice as Stories 2.1–3.1 (automated tests pass). rejected |
| B11 | Chosen purpose not remembered | low | one tap; Story 3.3 opens a purpose directly. rejected |
| B12 | Many taps to reach all-done | low | each choice is kept; a question step is a new design. rejected |
| B13 | `eu-eea-family-member` is a pointer counted as a document | medium | needs a design for non-tickable notes. deferred |
| B14 | Draft Thai wording (`ไม่เกี่ยวกับฉัน`, repeated `ครบ`) | low | raised with the user in the Thai review |

## Verification

**Commands:**
- `uv run pytest` -- all pass (Node tests included)
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- Demo mode, 360/320 px: open Checklist, choose family, tick 3 items and mark one "doesn't apply", close the browser, reopen: same state; back to chat mid-answer leaves the answer streaming.
