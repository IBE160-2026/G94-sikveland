# Story 2.3: feedback question at the end

## 2026-11-15 kl. 15:26 — WannapaS

### Task
Build Story 2.3: a done signal ("thank you", "ok", Thai variants) gets the feedback question with Yes/No buttons; the answer is stored for the adviser's success measure (SM-1, FR5).

### Plan
- `bmad-build` dispatch route with subagents (user approved), on `main`. Spec [spec-2-3-feedback-question-at-the-end.md](../../docs/implementation/spec-2-3-feedback-question-at-the-end.md).
- User decisions: "Yes" keeps the chat on screen and in the saved chats with a thank-you line, and the next question starts a new chat; spec kept whole (~1,950 tokens). From the PRD: a conversation is one visit, so new chat / reopen / Yes start a new `conversation_id`.

### Result
- Commit `56cd693` on `main` (not pushed): `done` in the classifiers (prompt v3) and the demo mock (punctuation/emoji-tolerant matching); `POST /api/feedback` with `FeedbackStore` port and SQLite adapter (`data/feedback.sqlite3`, only `conversation_id`, `answer`, `created_at`; `DATABASE_PATH` from the project root; 422/415/500 envelopes); page buttons, follow-up and thanks lines, `conversation_id` lifecycle; five new text keys and one privacy-notice sentence (Thai DRAFT); AD-6/AD-10, README with the SM-1 query, MT-14. Sprint status: Story 2.3 `review` (all of Epic 2 now in review).
- Review: 31 findings; 18 patched (notably blocking new questions and chat changes while a Yes is being sent, `conversation_id` reset in edge cases, privacy-notice sentence about the stored answer), 2 deferred (browser tests for the Yes/No flow), 2 false, the rest rejected with reasons in the spec.
- `uv run pytest`: 977 passed; ruff clean. Live Ollama check of classifier v3: 12/12 (thanks with emoji/punctuation → `done`; "thanks, and the fee?" and greetings → `general`; the other categories unchanged).

### Open items
- Approve the draft Thai texts: `feedback-question`, `feedback-follow-up`, `feedback-thanks`, `feedback-yes`, `feedback-no` and the new privacy-notice sentence (NFR8); the reviewer suggested less curt button labels than ใช่ / ไม่.
- Run MT-14 (demo, real key, Ollama).
