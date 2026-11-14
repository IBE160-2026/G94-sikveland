---
title: 'Story 1.7: Follow-up questions'
type: 'feature'
created: '2026-11-14'
status: 'done'
route: 'oneshot'
review_loop_iteration: 0
context:
  - '{project-root}/docs/implementation/epic-1-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Every question is sent with `history: []`, so a follow-up such as "and how much is the fee?" is answered without the earlier exchange, and a reload loses the conversation.

**Approach:** The server side already exists (Story 1.6: history filtered per turn, at most 10 items, alternating plain-text turns, no text stored or logged). The page now keeps the conversation in `sessionStorage` (AD-3): after `done` it stores `{question: meta.clean_question, answer: the exact text shown}` — fixed replies included, never after `error`; it sends the last 10 stored exchanges as `history`; on load it shows the stored conversation again and continues it. Closing the tab drops it (sessionStorage). The page also keeps each exchange's cited sources and the reminder flag locally so a reload shows the links again; only `{question, answer}` is sent to the server. Tests: string checks in `tests/test_static.py` and an API test that a follow-up's history reaches the model as alternating turns after filtering.

</frozen-after-approval>

## Implementation Notes
- `app/static/app.js`: `sessionStorage` key `conversation` holds `{question, answer, sources, reminder}` per exchange; `loadConversation` drops malformed or empty entries and returns `[]` when storage is blocked; `saveConversation` logs and carries on when storage fails or is full. `historyToSend` sends the last 10 as `{question, answer}`. The exchange is recorded during the stream (`meta.clean_question`, appended `text` deltas, `sources`) and stored only when `stream` returns true (after `done`) and both question and answer are non-empty. Storage keeps the last 50 exchanges (`MAX_STORED`) so a long session does not fill it; only the last 10 are sent. On load (and retry) `showConversation` replays stored exchanges with their reminder and source links; replayed links must be `https://`.
- `tests/test_static.py`: string checks for sessionStorage (and no localStorage), recording from `meta`/`text`, storing only after `done`, the 10-item `{question, answer}` history and the replay. `tests/test_chat_api.py`: a follow-up's history reaches the model in order, filtered.
- No server change: Story 1.6 already filters each history turn, limits it to 10 items and the adapter builds alternating turns (Story 1.5). The browser-level test stays deferred (deferred-work.md), so the page behaviour is checked by hand.
- `uv run pytest`: 451 passed.
- Review patches: `historyToSend` leaves out stored turns over the server limits (question 1000, answer 10000 characters), so one long turn cannot get every later question rejected; the page limits are tied to `app/web/chat.py` by a test. The record starts with an empty question and only a string `meta.clean_question` is stored. One `safeSources` check (https links with a title) for live and replayed sources; only title and URL are stored. The page scrolls to the newest exchange after a reload. The API test also has personal information in a history answer and checks that only the new question sets `personal_info_removed`. `uv run pytest`: 453 passed.

## Review Triage Log

Pass 1 (blind, 2026-11-14):

| # | Finding | Verdict | Evidence / route |
|---|---|---|---|
| 1 | One stored answer > 10000 chars or a clean question > 1000 chars gets every later question rejected with 422 | medium | the adapter allows 32000 output tokens; `A1234567` (8) becomes `[removed]` (9). patched (turns over the limits left out of `historyToSend`) |
| 2 | No way to start a new conversation except closing the tab | low | needs a new control and a new fixed Thai text (adviser review); with #1 fixed there is no stuck state left. rejected |
| 3 | Raw question stored if `meta` is missing; missing `clean_question` throws | low | the server always sends `meta` first, but storing raw text would be a privacy slip. patched |
| 4 | No scroll to the newest exchange after a reload | low | `showConversation` never scrolled. patched |
| 5 | Live and replayed sources checked differently; `id` stored unused | low | patched (one `safeSources`, title and URL only) |
| 6 | API test repeats an existing one; no personal info in a history answer; flag not checked | low | patched |
| 7 | Page tests only match source text; storage behaviour untested | medium | known; browser-level tests deferred. deferred (entry extended to Story 1.7 behaviour) |
| 8 | Deferred browser-test entry lists only Story 1.6 behaviour; no manual steps | low | deferred with #7; manual steps in issues.md |
| 9 | Page limit of 10 not tied to the server limit | low | patched (test compares the page constants with `app/web/chat.py`) |
| 10 | Question bubble shows raw text live and `clean_question` after a reload | low | intended: only the cleaned question is stored (AD-3). rejected |
| 11 | Spec and sprint status still in progress | false | the workflow sets both at finalize. rejected |
