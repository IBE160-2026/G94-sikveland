---
title: 'Story 3.3: Open the checklist from the chat'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '5c187457b3f23e45b3a70ad7417397cd7ef78431'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-3-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** After an answer about documents the applicant has to find the top-bar Checklist button and choose a purpose themselves; the answer does not lead to the list (FR6, AD-11).

**Approach:** The server sets `checklist: true` and `checklist_purposes` on the `sources` event when a cited source is linked to a checklist item; the page then shows an "Open checklist" button under that answer, which opens the checklist directly for one purpose or the purpose choice for several.

**Decision (user, 2026-11-15):** the button also comes back when a chat is reloaded or reopened from the saved chats: the page stores the answer's checklist purposes with the exchange on the device.

## Boundaries & Constraints

**Always:** `checklist_purposes` lists, in `VISIT_PURPOSES` order and without repeats, every purpose whose checklist has an item whose source id is among the answer's cited known sources; `checklist` is `true` exactly when that list is non-empty (AD-8); fixed replies, the no-answer reply and errors keep `checklist: false`, `checklist_purposes: []`; computed in `app/web` from the content store (only `app/web` builds stream events); works the same for Claude, Ollama and demo mode; the button text comes from a new text key (Thai DRAFT for the user's review, NFR8); the button opens the existing Story 3.2 checklist view (same focus, Escape and back behaviour; one purpose → that checklist directly, several → the purpose choice); the stored exchange gains its purposes, and on replay only known purposes are used (anything else is dropped, never breaks the page); a stored exchange without purposes (older chats) shows no button; ≥ 48 px, 320 px without sideways scroll; pure logic (validating stored purposes, deciding "one or choice") Node-tested; no change to what is sent to `/api/chat`.

**Never:** no LLM call to decide the button; no ticks or purposes sent to the server; no Thai in `app/static/`; no new dependency.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Family sources | answer cites `udi-sponsorship-form` (family, friends items) | `checklist: true`, `checklist_purposes: ["family","friends"]`; button → purpose choice | N/A |
| One purpose | cited source linked only to tourism items | `["tourism"]`; button opens tourism directly | N/A |
| General source | cites `embassy-visitor-visa-checklist` (all three) | all three, in order | N/A |
| No link | cites only `udi-fees` (no checklist item) | `checklist: false`, `[]`; no button | N/A |
| Fixed reply / no answer / error | any | `false`, `[]`; no button | N/A |
| Unknown cited id | dropped by the pipeline | not counted | N/A |
| Reload / reopen | saved exchange with purposes | button shown again under that answer | N/A |
| Old or bad storage | exchange without purposes, or `["visa"]`, or not a list | no button (unknown dropped) | N/A |
| While streaming | button tapped on an earlier answer | checklist opens; the answer keeps streaming | N/A |
| Demo | example about documents | button shown (mock sources) | N/A |

</frozen-after-approval>

## Code Map

- `app/web/chat.py` `_event` (`Sources` → `"checklist": False, "checklist_purposes": []` today, line ~216) -- compute from `event.items` ids and `content.checklists()`; the route has `state.content`; keep `_event` pure by passing a source-id → purposes map built once (e.g. at startup in `app/main.py` on `app.state`, or a helper in `app/web`).
- `app/ports/content.py` `VISIT_PURPOSES`, `ChecklistItem.source_id` -- reuse.
- `app/static/app.js` `handle` (`case "sources"` ~line 462), `createReply().sources`, `showConversation` (replay), `openChecklist`/`choosePurpose` from Story 3.2; `record` gets the purposes; `storeExchange` keeps them.
- `app/static/history.js` `validExchanges` -- keep the new field; `app/static/checklist.js` -- pure helpers (valid purposes, open target) + Node tests.
- `content/texts.yaml`, `app/ports/content.py` `REQUIRED_TEXT_KEYS` -- `checklist-open`.
- Tests: `tests/test_chat_api.py` (every server matrix row with `ScriptedLLM` and real checklists), `tests/test_demo_mode.py`, Node tests, `tests/test_static.py` source checks, `tests/test_texts_api.py`.
- Docs: README (button under answers), AD-8/AD-11 only if wording differs, manual test plan (new case), `deferred-work.md` browser-test entry extended by a new entry if needed.

## Tasks & Acceptance

**Execution:**
- [x] `app/web/chat.py` (+ wiring) -- checklist flags on `sources` -- AD-8, AD-11
- [x] `app/static/app.js`, `history.js`, `checklist.js`, `style.css` -- button, storage, replay -- FR6
- [x] `content/texts.yaml`, `app/ports/content.py` -- `checklist-open` -- AD-6, NFR8
- [x] Tests for every matrix row (pytest + Node) -- AD-13
- [x] Docs in the Code Map

**Acceptance Criteria:**
- Given the scripted fake citing a checklist-linked source and one that is not, when the tests run, then both cases are covered (story AC).
- Given a saved chat reopened days later, when it is shown, then the button under the documents answer opens the same checklist with its kept ticks.

## Implementation Notes

- `app/web/chat.py`: `checklist_purposes_by_source` builds a source id → purposes map once at startup (`app.state.checklist_purposes`, `app/main.py`); `checklist_purposes` orders by `VISIT_PURPOSES` without repeats; `_lines` forces `checklist: false`, `[]` on every non-answer reply. Same for Claude, Ollama and demo.
- Page: `checklist.js` `validPurposes` and `openTarget` (Node-tested); `app.js` adds the button under live and replayed answers, stores `checklistPurposes` with the exchange, returns focus to the opening button (or the top-bar button) on close. `history.js` already kept extra fields (comments only).
- No real source is linked only to tourism items, so the one-purpose row is tested with a custom map. `embassy-necessary-documents` maps to `family` only.
- New key `checklist-open` (Thai DRAFT). Docs: README, AD-3 (saved-exchange format) and AD-11, MT-16, a deferred browser-test entry. A one-off headless Edge run in demo mode at 320 px passed 18 checks. The implementer did not edit the spec; boxes and these notes were filled from the diff.

- The user approved the Thai button text `checklist-open` (เปิดรายการเอกสาร, with ": <purpose>" for one purpose) on 2026-11-15 (NFR8).

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V1 | The button wiring in `app.js` is pinned only by source text | medium | pre-verified gap; already recorded in `deferred-work.md` by this change (browser tests); MT-16 by hand |
| E1 | Button stays under a reply that errors or is cut after `sources` | low | the failed reply is never saved, so it vanishes on reload. patched (`reply.error()` removes it) |
| B1 | Spec in review while sprint status says in-progress | false | the workflow moves it to `review` at the end |
| B2 | "How to start" opens the family checklist directly for any applicant | medium | `embassy-necessary-documents` is used only by the `eu-eea-family-member` pointer item. deferred (with the Story 3.2 notes entry) |
| B3 | A tourism question still gets the three-purpose choice | low | the story's AC derives purposes from cited sources only. rejected |
| B4 | The button never says which checklist it opens; same accessible name for every button | low | patched (one purpose: "เปิดรายการเอกสาร: <purpose>") |
| B5 | Approval of the new Thai text untracked; README says other checklist texts are approved | false | the approval is asked of the user and tracked in `issues.md`; the other texts were approved in `5c18745` |
| B6 | MT-16 row omits the headless run | low | patched |
| B7 | MT-16 step 11 cannot fail | low | patched (read the shown sources first) |
| B8 | "No model call" test checks only answer calls | low | patched (`classify_calls == 1`) |
| B9 | Demo test copies the rule; the one-purpose demo path is not pinned | low | the only real one-purpose path is the B2 case, which is deferred to change; pinning it now would pin the behaviour to be changed. rejected |
| B10 | Focus moves twice when one checklist opens directly | low | patched |
| B11 | `NO_CHECKLISTS` / the map is a mutable dict | low | developer-only; tests swap the map on purpose. rejected |

## Verification

**Commands:**
- `uv run pytest` -- all pass (Node tests included)
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- Demo mode, 360/320 px: tap the documents example, tap "Open checklist" (purpose choice or direct), tick an item, go back, reload, tap the button again: same checklist and tick.
