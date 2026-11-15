---
title: 'Chat history on the device and a new-chat button'
type: 'feature'
created: '2026-11-15'
status: 'done'
route: 'dispatch'
baseline_commit: '7f8e0489259aa0b7a833ae64d8e40b712865a1b9'
review_loop_iteration: 0
context: []
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The page holds one conversation per tab (`sessionStorage`, AD-3): the only way to start over is to close the tab, and closing it loses everything, so an applicant cannot come back later to an answer they already got.

**Approach:** Keep past conversations in the browser's `localStorage` on the applicant's own device, in a list they can reopen and continue, and add a "new chat" button. The server stays stateless and stores nothing new.

**Decisions (user, 2026-11-15):**
- History is a saved list on the device (`localStorage`), surviving a closed tab; nothing is stored on the server. This replaces AD-3's "closing the tab drops it", so the privacy notice, PRD (NFR5, glossary "Conversation"), architecture (AD-3) and epics change with the code.
- Built on branch `chat-history` from `main`; merged only when the user decides.
- Layout: a slim top bar with a history button and a new-chat button; history opens a full-screen panel listing saved chats newest first (first question, shortened, and date), with a close button; tapping a chat reopens it.
- Deleting: a delete button on each saved chat and a delete-all button in the panel, each confirmed first (`window.confirm` with a fixed text). Deleting the open chat leaves an empty new chat.
- Keep the latest 20 chats (by last activity); saving a 21st drops the oldest.
- A fresh visit (new tab, later visit) opens an empty new chat; a reload keeps the open chat.
- A reopened chat can be continued; follow-ups use its last 10 exchanges.

## Boundaries & Constraints

**Always:** the request stays `{question, history}` with at most the last 10 exchanges of the *open* conversation (AD-3); an exchange is stored only after `done`, with `clean_question` and the shown text (AD-3, AD-4); all visible text comes from `/api/texts` (AD-6), new Thai texts in `content/texts.yaml` with `en`, reviewed by the user/adviser before merge (NFR8); no new dependency, no framework; works at 360 px, no horizontal scroll at 320 px, touch targets ≥ 48 px (NFR1); unreadable or malformed stored data is skipped, never breaks the page; storage blocked or full → the answer is still shown.

**Never:** no server-side change to `/api/chat` or the request log; no history sent other than the open conversation; no Thai in `app/static/`; no change to Story 2.3's future `conversation_id` (AD-10) beyond noting it.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| First question | empty chat | after `done`, a new conversation (local id, time, exchanges) is saved and appears first in the list | storage full → answer shown, not saved |
| Follow-up | open conversation | exchange appended; conversation moves to the top of the list | N/A |
| New chat | tap new-chat | empty chat with example questions; list unchanged | disabled while answering |
| Reopen | tap a list item | its exchanges shown with sources and reminders; next question continues it with its last 10 | disabled while answering |
| Reload | open conversation | same conversation shown | N/A |
| Error turn | `error` event | nothing saved; an empty new chat creates no list item | N/A |
| Old data | `sessionStorage` `conversation` from before | moved into the list once, then removed | malformed → dropped |
| Malformed | broken JSON / wrong shapes in `localStorage` | bad entries skipped, rest shown | N/A |
| 21st chat | 20 saved, a new chat gets its first `done` | oldest by last activity dropped | N/A |
| Delete one | confirm yes / no | removed from list and storage / nothing changes; the open chat deleted → empty new chat | N/A |
| Delete all | confirm yes | list empty, storage key removed, empty new chat | N/A |
| Fresh visit | new tab, saved chats exist | empty new chat; chats in the panel | N/A |
| Other tab | two tabs open | each tab keeps its own open chat; a save re-reads the list first so the other tab's chats are not overwritten | N/A |

</frozen-after-approval>

## Code Map

- `app/static/app.js` -- `STORAGE_KEY "conversation"` + `loadConversation`/`saveConversation` (sessionStorage) become a conversation list in `localStorage` plus the open conversation's id in `sessionStorage`; reuse `safeSources`, `createReply`, `showConversation`, `historyToSend` (keep its limit filters), `setAnswering` (also disable new-chat/history controls). `MAX_STORED = 50` exchanges per conversation stays.
- `app/static/index.html`, `app/static/style.css` -- new controls and the list; mobile-first, follow existing button styles (`.example-question`, `.send`).
- `content/texts.yaml` + `app/ports/content.py` `REQUIRED_TEXT_KEYS` -- closed key list: add `history-button`, `new-chat-button`, `history-title`, `history-close`, `history-empty`, `delete-chat`, `delete-all-chats`, `confirm-delete-chat`, `confirm-delete-all-chats` (Thai drafted by the implementer, marked for the user's review); extend `privacy-notice` (th + en) with "your questions and answers are saved on this device only; anyone using it can read them".
- Testability: no JS test runner exists (Playwright is deferred). Put the storage logic (load/validate, save with re-read, cap 20, delete one/all, migration, history to send) as pure functions taking a storage object in a new `app/static/history.js`, loaded before `app.js` and also usable from Node (`module.exports` when defined); test it from pytest by running `node` in a subprocess with an in-memory storage, skipping only when `node` is not on PATH (it is locally and on GitHub's ubuntu runners). Cover every matrix row there; keep UI wiring in `app.js`.
- `tests/test_static.py:159-207` -- string checks that assert sessionStorage and *no* `localStorage` (AD-3); rewrite for the new rule. `tests/test_texts_api.py`, content tests -- new keys.
- Docs: `ARCHITECTURE-SPINE.md` AD-3 (+ runtime view line ~191), `prd.md` NFR5 + glossary "Conversation" + FR1, `epics.md` Story 1.7 ("closing the tab removes it") and the AD-3 line, `README.md` (status, privacy), `manual-test-plan.md` MT-07 step 4 and a new case.

## Tasks & Acceptance

**Execution:**
- [x] `content/texts.yaml`, `app/ports/content.py` -- new keys and privacy-notice text -- AD-6, NFR8
- [x] `app/static/app.js`, `index.html`, `style.css` -- list storage, migration, new chat, history UI -- the feature
- [x] `tests/test_static.py`, `tests/test_texts_api.py` -- matrix rows as source checks; new keys served -- CI
- [x] Docs listed in Code Map -- keep AD-3/NFR5/epics/README/test plan true

**Acceptance Criteria:**
- Given a saved conversation, when the tab is closed and the page opened again, then it is in the list and can be reopened and continued.
- Given any state, when `/api/chat` is called, then the body holds only the open conversation's last ≤ 10 exchanges.
- Given the page at 320 px, when the list is open, then nothing scrolls sideways.

## Implementation Notes

- Storage: `localStorage["conversations"]` = `[{id, updated, exchanges}]` (newest first, cap 20, 50 exchanges each); `sessionStorage["open-conversation"]` = id of the open chat. Old `sessionStorage["conversation"]` is migrated once and opened, then removed (kept if the list is full, so it is retried).
- `app/static/history.js` holds the pure storage functions (exported for Node), including `appendExchange` (append, cap 50, save, mark open) and `startOpen` (migrate, then open); `app.js` keeps the open chat in memory as well, so follow-ups still work when storage is blocked or full. A save re-reads the list and writes the open chat whole. A chat gets its id only once saved; if that id is no longer in the list (deleted in another tab, or dropped by the cap of 20), the next exchange starts a new chat instead of bringing the deleted one back.
- The list `id` is local only (`Date.now` + random), not the AD-10 `conversation_id`; noted in AD-3.
- Date in the list: `toLocaleDateString` with the page's `lang` (`th`), e.g. "15 พ.ย. 2569". Question shortened to 80 characters plus a two-line clamp.
- The demo label now sits in a sticky `<header class="top">` with the top bar; `tests/test_demo_mode.py` checks the header instead of `.demo-label`.
- Thai texts for the 9 new keys and the privacy-notice sentence are drafts marked in `content/texts.yaml`, awaiting user/adviser review (NFR8).
- Verified also in headless Edge (demo mode, 320 px) with a one-off CDP script: every matrix row passed; not part of CI.

## Spec Change Log

## Review Triage Log

Pass 1 (blind, edge case, verification gap; 2026-11-15). B = blind, E = edge case, V = verification gap.

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| V1 | `app.js` open-chat logic (append, open id, migrate order) checked only by source strings | medium | pre-verified gap: `[record]` for `concat`, a dropped `setOpenId` or swapped startup calls pass CI. patched (`appendExchange`, `startOpen` in history.js, Node tests) |
| V2 | Node tests skip silently when node is missing, also in CI | medium | pre-verified gap; `skipif` with no CI guard. patched (fail when `CI` is set) |
| V3 | No test that a turn exactly at 1000/10000 chars is still sent | low | pre-verified gap; direct test addition. patched |
| V4 | Tapping a chat that is gone closes the panel and opens nothing | low | `reopenChat` called `closeHistory()` before `renderHistoryList()`. patched (with B3, E6) |
| V5 | A chat deleted in another tab comes back | medium | same root as B1. patched |
| B1 | A tab re-saves a chat another tab deleted (one or all) | medium | `storeExchange` saved the whole in-memory chat; `saveConversation` re-read only other ids; undoes a deliberate delete on a shared device. patched: an id no longer in the list starts a new chat with only the new exchange |
| B2 | Same chat in two tabs: the later save overwrites the other's follow-ups | low | real, but two tabs on one chat is rare on a phone and the fix needs merge logic. rejected |
| B3 | Reopening a gone chat gives no feedback | low | same as V4. patched |
| B4 | `aria-modal` panel does not trap focus; a question can be sent behind it | low | Tab reached `main` and the form. patched (`inert` on header, main, form while open) |
| B5 | Failed saves/deletes are silent | low | the approved intent accepts "storage blocked or full → the answer is still shown"; a smaller write cannot hit the quota and blocked storage lists nothing to delete. rejected |
| B6 | `window.confirm` may be suppressed in in-app browsers or by "prevent dialogs" | maybe-false | the approved decision uses `window.confirm`; needs a real-phone check. deferred (medium, unverified) |
| B7 | Failed migration hides the old conversation | low | needs `localStorage` full or blocked on the first load after the update while `sessionStorage` works; unlikely, fix adds a branch. rejected |
| B8 | Privacy sentence "saved on this device only" reads as a promise about the AI service; no retention or delete hint | low | wording sits right after "sent to an AI service". patched (th + en, still DRAFT) |
| B9 | `epic-1-context.md:44` still says sessionStorage, closing the tab drops it | low | verified at that line. patched |
| B10 | AD-10 / Story 2.3 ("Yes" clears the history, `conversation_id` in sessionStorage) undefined with saved chats; untracked | medium | the spine defers it to Story 2.3 with no tracking entry. deferred |
| B11 | MT case misses two tabs, private mode, migration | low | patched (two-tab delete and private-window steps); also renumbered MT-10 → MT-11 to avoid the `ollama` branch's MT-10 |
| B12 | Node tests can be skipped unnoticed | medium | same as V2. patched |
| B13 | Spec task list omits history.js and test_history_js.py | low | fix edits this build's spec. rejected |
| B14 | List does not mark the open chat; same-day chats only differ by title | low | cosmetic; delete is confirmed first. rejected |
| B15 | Source-string tests depend on exact whitespace | low | real but developer-only; V1 moved the main logic to Node tests. rejected |
| E1 | `history.js` missing (stale cached `index.html`) → blank page, no retry | maybe-false | StaticFiles sends no Cache-Control, so a stale page is possible; needs a browser upgrade test. deferred (medium, unverified) |
| E2 | Same chat in two tabs loses follow-ups | low | same as B2. rejected |
| E3 | Deleted chat re-saved by another tab | medium | same as B1. patched |
| E4 | Quota reached: nothing saved again, no eviction | low | 20 chats of typical length are far below 5 MB; fix adds a retry loop. rejected |
| E5 | Failed migration hides old conversation | low | same as B7. rejected |
| E6 | Panel closes before the refreshed list renders | low | same as V4. patched |
| E7 | Focus leaves the modal panel; question sent behind it | low | same as B4. patched |
| E8 | Delete write fails → open chat cleared though still saved | false | a shorter `setItem` cannot exceed the quota, and blocked storage lists nothing, so there is nothing to delete |
| E9 | Claim "other tab … not overwritten" fails for the same id and deleted ids | medium | deleted-id part same as B1 (patched); same-id part same as B2 (rejected) |
| E10 | Claim "delete removes from storage" fails with a second tab open | medium | same as B1. patched |
| E11 | Claim "drop the oldest" does not cover quota failure | low | same as E4. rejected |

## Verification

**Commands:**
- `uv run pytest` -- all pass
- `uv run ruff check` and `uv run ruff format --check` -- clean

**Manual checks (if no CLI):**
- Demo mode, 360/320 px: ask, new chat, ask, close tab, open the page again (empty chat), open the first chat from the panel and ask a follow-up; reload keeps it; delete one, then delete all.
