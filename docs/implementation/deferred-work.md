# Deferred Work

- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Resolve `DATABASE_PATH` against the project root, not the working directory, when Story 2.3 creates the SQLite file.
  evidence: `database_path` is the relative string `data/feedback.sqlite3`; started from another folder, the feedback file would be created in the wrong place. Nothing uses it before Story 2.3.
- source_spec: `docs/implementation/spec-1-2-chat-page-with-thai-texts.md`
  summary: Add a browser-level test (e.g. Playwright via pytest) for the chat page's JavaScript in Story 1.6: rendering from `/api/texts`, tap-to-fill, the retry button on load failure, and the streamed answer.
  evidence: No test runs `app/static/app.js`; changing `example.text` to `example.th`, dropping the tap handler, or removing `loadFailed.hidden = false` all pass CI. Story 1.6 adds much more page logic (stream reading), so the gap grows there.
- source_spec: `docs/implementation/spec-1-3-knowledge-base-of-official-sources.md`
  summary: Add a VFS Global source (the Thailand–Norway booking/info page) to the knowledge base, so the "book an appointment at VFS" step can link to VFS (FR12).
  evidence: VFS (Cloudflare) answers the ingest client with HTTP 403, the old VFS PDF stated an outdated fee (EUR 80), and the current VFS page is a JavaScript app that could not be saved from the browser; the user dropped VFS for now on 2026-11-13. `PUBLISHER_DOMAINS` still allows `vfsglobal.com`.
- source_spec: `docs/implementation/spec-1-4-personal-information-filter.md`
  summary: Some real Thai ID spellings get through the filter: `1 234567890123`, `1-2345-67890-123`, `1 2345 67890 123`, `12-3456-78901-2-3`, IDs after a 5-digit group (`10110 1234 5678 90123` → `[removed] 90123`), separators outside `SEP` (en space, soft hyphen, word joiner, full-width dot), and passports written `AA: 1234567`.
  evidence: Review pass 4, confirmed by probe on 2026-11-14 (triage #8, #9, #11, #12). The user chose to accept the loop 3 rules because of the 2026-11-15 deadline. A possible fix: accept a 1-digit first group with any 3+ grouping after it, prefer windows that end at a run boundary, widen `SEP`, allow `:` as a passport separator.
- source_spec: `docs/implementation/spec-1-4-personal-information-filter.md`
  summary: The filter removes some phone numbers and amounts it should keep: 13-digit phone spellings starting with `0066`, numbers in 3+ digit groups that add up to 13 (`room 123 0812345678`, `500000-1500000 baht`, `2569 2026 12345`, `021234567 2569`), and glued lowercase amounts (`kr1500000`, `Rs1500000`, `No1234567`).
  evidence: Review pass 4, confirmed by probe on 2026-11-14 (triage #6, #7, #10). This contradicts the Decision that phone numbers are not removed. A possible fix: Thai IDs start with 1–8, so a group starting with 0 cannot open an ID; the glued passport form should need uppercase letters. Check against the evaluation test set before changing.
- source_spec: `docs/implementation/spec-1-5-claude-connection-with-a-test-version.md`
  summary: Set an explicit timeout and `max_retries` on the Anthropic client, and let Story 1.6 tell overload (429/529) from configuration errors (400/401) without user text.
  evidence: The adapter uses the SDK defaults (10-minute timeout, 2 silent retries) and `LLMError` keeps only the exception class name. The right values depend on the stream UX in Story 1.6 (adaptive thinking can pause before the first text).
- source_spec: `docs/implementation/spec-1-6-streamed-answer-with-sources.md`
  summary: Timeouts for a stalled answer: explicit timeout and `max_retries` on the Anthropic client, a page-side `AbortController` deadline that shows the fixed error text, and, if the real-phone test shows idle cuts, a heartbeat line while text is held back. Also check that a client disconnect closes the model stream.
  evidence: Review pass 1 of Story 1.6 (#3, #4, #5, #11). Today a stalled call keeps the typing dots and a locked form until the SDK default (10 minutes, 2 retries). The values need the real-phone test in Facebook's in-app browser; replaces the Story 1.5 entry's target.
- source_spec: `docs/implementation/spec-1-6-streamed-answer-with-sources.md`
  summary: Browser-level tests for the chat page's JavaScript (stream parsing across chunks, append-only text, reminder, sources, error text, form re-enabled), after part 1.
  evidence: Review pass 1 of Story 1.6 (#12): `tests/test_static.py` only matches strings in `app.js`; breaking line buffering or `setAnswering(false)` passes CI. Replaces the Story 1.2 entry's Story 1.6 target.
- source_spec: `docs/implementation/spec-1-7-follow-up-questions.md`
  summary: Extend the deferred browser-level page tests to Story 1.7: exchange stored in sessionStorage only after `done`, follow-up sends the last 10, reload replays the conversation with reminder and sources, closing the tab drops it, malformed stored entries ignored.
  evidence: Review of Story 1.7 (#7, #8): `tests/test_static.py` only matches strings in `app.js`; e.g. `slice(MAX_HISTORY)` instead of `slice(-MAX_HISTORY)` would pass CI.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Saved chats changed the Story 1.7 entry above: closing the tab no longer drops the conversation (a new tab opens an empty new chat; past chats stay in `localStorage`). The storage logic in `app/static/history.js` is tested in Node (`tests/test_history_js.py`); the UI wiring in `app.js` (top bar, history panel, reopen, delete with confirm, controls disabled while answering) still needs the deferred browser-level tests.
  evidence: No browser test runner (Playwright deferred); `tests/test_static.py` only matches strings in `app.js`. A one-off headless-browser run passed on 2026-11-15 but is not in CI.
- source_spec: `docs/implementation/spec-4-2-demo-mode-without-an-api-key.md`
  summary: In Story 2.3, make done-phrase matching ignore surrounding punctuation and emoji (`Thanks!`, `ok.`, `ขอบคุณค่ะ 🙏`), in the mock and in the real classifier's tests, and test a stored demo category other than `general`.
  evidence: Review of Story 4.2 (#17, #22): the mock matches done phrases exactly after trimming and casefolding; nothing consumes `classify` yet.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Check the Ollama context budget in a long conversation (system ~24,700 tokens + up to 10 history turns + thinking + answer within `OLLAMA_NUM_CTX` 32768), and detect a full context at runtime (e.g. `prompt_eval_count` reaching `num_ctx`) instead of letting Ollama truncate silently.
  evidence: Review of the Ollama build (#3), medium, unverified: 32768 − ~24,700 leaves ~8k tokens; the probe's documents question used ~2,700 thinking tokens; never run with 10 long turns. Settle with a 10-turn manual run against Ollama.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Cap an Ollama answer (`num_predict` and/or an overall deadline), so a model stuck thinking cannot hold a request open; the read timeout restarts on every thinking line.
  evidence: Review of the Ollama build (#5), medium, unverified: no cap is sent and thinking lines are not shown, so the applicant would see only typing dots. Settle by forcing a long thinking run.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: On slow or CPU-only machines, the first (uncached) ~24,700-token prompt may take longer than the 300 s read timeout before Ollama sends anything; make the timeout a setting or separate the first-byte wait.
  evidence: Review of the Ollama build (#6), medium, unverified: 7 s on the user's GPU; no measurement on CPU. Settle by timing a cold request on a CPU-only machine.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Check that Ollama follow-up questions still cite: earlier answers go back as history without `[[id]]` markers, which may teach a small model to stop citing (then every follow-up becomes `reply-no-answer`).
  evidence: Review of the Ollama build (#8), medium, unverified: the manual run was single-turn only. Settle with a follow-up question against Ollama; if it fails, re-insert markers in history or add a reminder after it.
- source_spec: `docs/implementation/spec-ollama-provider.md`
  summary: Browser check of the example questions with `LLM_PROVIDER=ollama` (AC 4): run MT-10 in `manual-test-plan.md` and record the result.
  evidence: Review of the Ollama build (#11): AC 4 was checked through the app by script, not tapped in a browser. The docs part of this entry (README, manual test plan, spine, PRD addendum, spec-1-6 and spec-1-8 change logs) was done on 2026-11-15.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Settle how Story 2.3's feedback flow fits saved chats: AD-10 and epics Story 2.3 say "Yes" ends the conversation and "the page clears the history", and `conversation_id` lives in `sessionStorage`; with saved chats it is undefined whether "Yes" deletes, closes or keeps the saved chat, and what `conversation_id` does on "new chat" or when an older chat is reopened.
  evidence: Review of the saved-chats build (blind #10): the spine only says "Story 2.3 decides how they relate"; nothing else tracks it, so it would be missed when Story 2.3 is built.
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: Delete uses `window.confirm`; check that it works in Facebook's and LINE's in-app browsers and after a user ticks "prevent this page from creating additional dialogs" (then `confirm` returns false at once and delete silently does nothing). If it fails, use an in-page confirm built from the existing text keys.
  evidence: Review of the saved-chats build (blind #6), medium, unverified: the decision to use `window.confirm` is in the approved spec; whether in-app webviews suppress it needs a real-phone test (MT-09 setup).
- source_spec: `docs/implementation/spec-chat-history-and-new-chat.md`
  summary: If `history.js` is missing when `app.js` runs (a stale cached `index.html` without the new script tag after the update), `window.ChatHistory` is undefined, `startOpenChat` throws before `load()`, and the page stays blank with no retry button; guard it or send `Cache-Control: no-cache` for the static files.
  evidence: Review of the saved-chats build (edge #1), medium, unverified: FastAPI's StaticFiles sends ETag/Last-Modified but no Cache-Control, so browsers may serve a stale `index.html` heuristically; settle by loading the old page in a browser, updating, and reloading once.
