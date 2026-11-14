# Story 1.6: Streamed answer with sources

## 2026-11-14 kl. 22:27 — WannapaS

### Task
Implement Story 1.6 from its spec (dispatched implementation step): `POST /api/chat` that filters the question and history, answers through the `LLMClient` with the grounding rule (AD-7) and streams JSON Lines events (AD-8); the page sends questions (typed or tapped examples), shows a typing indicator, appends text as it arrives and lists source links.

### Plan
- Spec: [spec-1-6-streamed-answer-with-sources.md](../../docs/implementation/spec-1-6-streamed-answer-with-sources.md); context: [epic-1-context.md](../../docs/implementation/epic-1-context.md).
- Pipeline first (domain events + `answer_question`), then the web route and event mapping, then wiring in `create_app`, then the page, then tests for every matrix row.

### Result
- New: `app/pipeline/answer.py` (`Meta`, `TextDelta`, `SourceRef`, `Sources`, `Done`, `Failed(reason)`, `answer_question`), `app/web/chat.py` (`POST /api/chat`, pydantic request model, `StreamingResponse` `application/jsonl`, `Cache-Control: no-store`, `X-Accel-Buffering: no`), `tests/test_answer_pipeline.py`, `tests/test_chat_api.py`.
- Changed: `app/main.py` (`create_app(settings, llm=None)`, default `AnthropicLLM`, answer prompt loaded at startup and kept on `app.state.answer_prompt`, app-wide 422 handler `{"error": {"code": "invalid_request", ...}}`, chat router), `app/static/app.js` (send on submit and example tap, form disabled while answering, question bubble, CSS typing dots, `fetch` + `getReader()` + `TextDecoder` stream mode, reminder above the reply, append-only text, source links `target="_blank" rel="noopener"`, fixed error text), `app/static/style.css` (bubbles, reply, reminder, typing animation, 48 px source links), `tests/test_static.py` (stream reading, append-only, safe links). `index.html` unchanged. Spec tasks ticked and Implementation Notes added.
- Beyond the spec: `Failed` carries a `reason` (exception class name or `unknown source id`) so `app/web` can log failures without text.
- `uv run pytest`: 436 passed, no network, no key. Live check with uvicorn and a slow fake model: `meta` arrives at once, each `text` line arrives as the model yields it, Thai sent as UTF-8. `node --check` on `app.js` passes.
- Review fixes: 422 no longer echoes extra-key names (`unknown field: ...`); history turns are stripped and limited (question 1-1000, answer 1-10000 characters); the page keeps a typed draft on example taps, puts the question back after any failure, cancels the reader when reading stops early, and sets `aria-busy` on `#messages` while answering. `tests/test_chat_api.py` + `tests/test_static.py`: 71 passed.
- Not committed (left for the caller/review step).

### Open items
- Manual check in a browser at 360/320 px (typing dots, Thai text in parts, source links, no horizontal scroll; without key the fixed error text) and with a real API key: not run here.
- Manual check on a real phone in Facebook's in-app browser (AC, to be noted in the PR) — already tracked from the architecture log.
