# Story 1.7: Follow-up questions

## 2026-11-14 kl. 22:36 — WannapaS

### Task
Push Story 1.6 and implement Story 1.7: follow-up questions such as "and how much is the fee?" use the earlier exchanges, and a reload in the same tab keeps the conversation.

### Plan
- `bmad-build`, one-shot route (page-only change; the server already filters and limits history since Story 1.6). Spec: [spec-1-7-follow-up-questions.md](../../docs/implementation/spec-1-7-follow-up-questions.md).
- Implement in `app/static/app.js`, string checks in `tests/test_static.py`, one API test, then one blind review.

### Result
- Pushed Story 1.6 (`0d8636b` on origin/main).
- `app/static/app.js`: conversation in `sessionStorage` (key `conversation`); stored after `done` only (clean question, exact shown text incl. fixed replies, sources, reminder flag); last 10 sent as `{question, answer}`, turns over the server limits left out; reload replays the conversation with reminder and source links and scrolls to the end; one `safeSources` check for live and replayed links; storage errors do not break answering.
- Tests: page limits tied to `app/web/chat.py`; follow-up history reaches the model in order and filtered (question and answer), flag only from the new question. `uv run pytest`: 453 passed.
- Review (blind, 11 findings): 6 patched, 2 deferred (browser-level tests extended to Story 1.7), 3 rejected.
- Committed to main as `1cedc9d`. Spec `done`, sprint status `review`. Not pushed.

### Open items
- Manual check in a browser: send a follow-up ("and the fee?"), reload (conversation and links back), close the tab (gone), an error turn is not stored.
