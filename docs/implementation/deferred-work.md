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
