# Deferred Work

- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Resolve `DATABASE_PATH` against the project root, not the working directory, when Story 2.3 creates the SQLite file.
  evidence: `database_path` is the relative string `data/feedback.sqlite3`; started from another folder, the feedback file would be created in the wrong place. Nothing uses it before Story 2.3.
- source_spec: `docs/implementation/spec-1-1-project-skeleton-with-ci.md`
  summary: Add a test that only `app/adapters/anthropic_llm.py` imports `anthropic` and that `app/pipeline/` imports neither FastAPI nor the SDK, in Story 1.5.
  evidence: The architecture's main layer rules are backed only by docstrings; the first `anthropic` import arrives in Story 1.5. Story 1.5 should also clear `ANTHROPIC_AUTH_TOKEN` in tests, since the SDK reads it and `ant` profiles as well as `ANTHROPIC_API_KEY`.
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
